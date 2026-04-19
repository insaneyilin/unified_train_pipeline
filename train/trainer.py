import logging
import random
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import torch
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader
from torch.utils.data.distributed import DistributedSampler

from unified_train_pipeline.core.dict_config import DictConfig
from unified_train_pipeline.hooks.hook_runner import HookRunner
from unified_train_pipeline.interfaces.checkpoint_io import LocalCheckpointIO
from unified_train_pipeline.registry.dataset_register import build_dataset
from unified_train_pipeline.registry.module_register import build_module
from unified_train_pipeline.train.distributed import (cleanup_distributed,
                                                      get_local_rank, get_rank,
                                                      get_world_size,
                                                      init_distributed,
                                                      synchronize)
from unified_train_pipeline.train.loop import (normalize_batch_to_data_dict,
                                               to_device)

logger = logging.getLogger("unified_train_pipeline")


class Trainer:
    """Generic config-driven trainer with optional DDP."""

    def __init__(self, config: DictConfig):
        self.config = config
        self.rank = 0
        self.world_size = 1
        self.device = self._setup_device()
        self.distributed = bool(self.config.train.get("distributed", False))
        self._scaler = torch.cuda.amp.GradScaler(enabled=bool(
            self.config.train.get("amp", False)))
        self._hook_runner = HookRunner()
        self._checkpoint_io = LocalCheckpointIO()

        self.model = None
        self.loss_module = None
        self.optimizer = None
        self.lr_scheduler = None
        self.train_loader = None
        self.global_step = 0

    def _setup_device(self) -> torch.device:
        if torch.cuda.is_available():
            return torch.device("cuda")
        if hasattr(torch.backends,
                   "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")

    def _setup_seed(self, seed: int):
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)

    def _build_train_loader(self):
        dataset_cfg = self.config.dataset
        dataset = build_dataset(dataset_cfg.name, dataset_cfg, self.config)
        sampler = None
        if self.distributed:
            sampler = DistributedSampler(dataset,
                                         num_replicas=self.world_size,
                                         rank=self.rank,
                                         shuffle=True)
        collate_fn = getattr(dataset, "collate_fn", None)
        self.train_loader = DataLoader(
            dataset,
            batch_size=int(dataset_cfg.get("batch_size", 32)),
            shuffle=(sampler is None),
            sampler=sampler,
            num_workers=int(self.config.train.get("num_workers", 2)),
            collate_fn=collate_fn,
            drop_last=bool(dataset_cfg.get("drop_last", False)),
        )

    def _build_model_and_loss(self):
        model_cfg = self.config.model
        self.model = build_module(model_cfg.name, model_cfg, self.config).to(
            self.device)
        if self.distributed:
            ddp_kwargs = {"find_unused_parameters": False}
            if self.device.type == "cuda":
                self.model = DDP(self.model,
                                 device_ids=[get_local_rank()],
                                 **ddp_kwargs)
            else:
                self.model = DDP(self.model, **ddp_kwargs)

        if "loss" in self.config and self.config.loss is not None:
            self.loss_module = build_module(self.config.loss.name,
                                            self.config.loss,
                                            self.config).to(self.device)

    def _build_optimizer(self):
        optimizer_name = self.config.optimizer.get("name", "adam").lower()
        lr = float(self.config.optimizer.get("lr", 1e-3))
        weight_decay = float(self.config.optimizer.get("weight_decay", 0.0))
        if optimizer_name == "adam":
            self.optimizer = torch.optim.Adam(self.model.parameters(),
                                              lr=lr,
                                              weight_decay=weight_decay)
        elif optimizer_name == "sgd":
            momentum = float(self.config.optimizer.get("momentum", 0.9))
            self.optimizer = torch.optim.SGD(self.model.parameters(),
                                             lr=lr,
                                             momentum=momentum,
                                             weight_decay=weight_decay)
        else:
            raise ValueError(f"Unsupported optimizer: {optimizer_name}")

    def _setup_runtime(self):
        self._setup_seed(int(self.config.get("seed", 42)))
        if self.distributed:
            init_distributed()
            self.rank = get_rank()
            self.world_size = get_world_size()
            if torch.cuda.is_available():
                self.device = torch.device(f"cuda:{get_local_rank()}")
        self._build_train_loader()
        self._build_model_and_loss()
        self._build_optimizer()

        if self.rank == 0:
            logging.basicConfig(level=logging.INFO,
                                format="[%(asctime)s][%(levelname)s] %(message)s")

    def _compute_loss(self, data_dict: Dict[str, Any]) -> Dict[str, torch.Tensor]:
        if self.loss_module is not None:
            return self.loss_module(data_dict)
        if "_loss_dict" in data_dict:
            return data_dict["_loss_dict"]
        if "total_loss" in data_dict:
            return {"total_loss": data_dict["total_loss"]}
        raise ValueError(
            "No loss module configured and model output does not contain total_loss."
        )

    def _save_checkpoint(self):
        if self.rank != 0:
            return
        output_dir = Path(self.config.train.get("output_dir", "outputs"))
        checkpoint_path = output_dir / "checkpoints" / f"step_{self.global_step}.pt"
        model_state = self.model.module.state_dict() if isinstance(
            self.model, DDP) else self.model.state_dict()
        checkpoint = {
            "global_step": self.global_step,
            "model": model_state,
            "optimizer": self.optimizer.state_dict(),
            "config": self.config.to_dict(),
        }
        self._checkpoint_io.save(checkpoint, str(checkpoint_path))
        logger.info("Saved checkpoint to %s", checkpoint_path)

    def _train_one_batch(self, batch: Any, context: Dict[str, Any]) -> Optional[float]:
        data_dict = normalize_batch_to_data_dict(batch)
        data_dict = to_device(data_dict, self.device)
        data_dict = self._hook_runner.run_before_iteration(data_dict, context)

        self.optimizer.zero_grad(set_to_none=True)
        use_amp = bool(self.config.train.get("amp", False)) and self.device.type == "cuda"
        with torch.cuda.amp.autocast(enabled=use_amp):
            data_dict = self.model(data_dict)
            data_dict = self._hook_runner.run_after_forward(data_dict, context)
            loss_dict = self._compute_loss(data_dict)
            data_dict["_loss_dict"] = loss_dict
            total_loss = loss_dict["total_loss"]

        if use_amp:
            self._scaler.scale(total_loss).backward()
            if self.config.train.get("gradient_clip_norm") is not None:
                self._scaler.unscale_(self.optimizer)
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(),
                    float(self.config.train.get("gradient_clip_norm")))
            self._scaler.step(self.optimizer)
            self._scaler.update()
        else:
            total_loss.backward()
            if self.config.train.get("gradient_clip_norm") is not None:
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(),
                    float(self.config.train.get("gradient_clip_norm")))
            self.optimizer.step()

        self.global_step += 1
        data_dict = self._hook_runner.run_after_step(data_dict, context)
        return float(total_loss.detach().item())

    def train(self):
        self._setup_runtime()
        max_epochs = int(self.config.train.get("max_epochs", 1))
        max_steps = int(self.config.train.get("max_steps", 0))
        log_interval = int(self.config.train.get("log_interval", 20))
        save_interval = int(self.config.train.get("save_interval", 200))
        self.model.train()

        try:
            for epoch in range(max_epochs):
                if self.distributed and isinstance(self.train_loader.sampler,
                                                   DistributedSampler):
                    self.train_loader.sampler.set_epoch(epoch)

                for batch_idx, batch in enumerate(self.train_loader):
                    context = {
                        "epoch": epoch,
                        "batch_idx": batch_idx,
                        "global_step": self.global_step,
                        "rank": self.rank,
                    }
                    loss_value = self._train_one_batch(batch, context)
                    if self.rank == 0 and self.global_step % log_interval == 0:
                        logger.info(
                            "epoch=%d batch=%d step=%d loss=%.6f",
                            epoch,
                            batch_idx,
                            self.global_step,
                            loss_value,
                        )
                    if self.global_step > 0 and self.global_step % save_interval == 0:
                        self._save_checkpoint()

                    if max_steps > 0 and self.global_step >= max_steps:
                        break

                synchronize()
                if max_steps > 0 and self.global_step >= max_steps:
                    break
        finally:
            if self.distributed:
                cleanup_distributed()
