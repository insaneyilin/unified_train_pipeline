import logging
import random
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import torch
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader
from torch.utils.data.distributed import DistributedSampler
from torch.utils.tensorboard import SummaryWriter

from unified_train_pipeline.core.dict_config import DictConfig
from unified_train_pipeline.hooks.hook_runner import HookRunner
from unified_train_pipeline.interfaces.checkpoint_io import LocalCheckpointIO
from unified_train_pipeline.registry.dataset_register import build_dataset
from unified_train_pipeline.registry.evaluator_register import build_evaluator
from unified_train_pipeline.registry.module_register import build_module
from unified_train_pipeline.registry.visualizer_register import build_visualizer
from unified_train_pipeline.train.distributed import (cleanup_distributed,
                                                      ddp_all_reduce_sum,
                                                      get_local_rank, get_rank,
                                                      get_world_size,
                                                      init_distributed,
                                                      synchronize)
from unified_train_pipeline.train.loop import (normalize_batch_to_data_dict,
                                               to_device)
from unified_train_pipeline.train.validation_report import ValidationReportWriter

logger = logging.getLogger("unified_train_pipeline")


class Trainer:
    """Generic config-driven trainer with optional DDP."""

    def __init__(self, config: DictConfig):
        self.config = config
        self.rank = 0
        self.world_size = 1
        self.device = self._setup_device()
        self.distributed = bool(self.config.train.get("distributed", False))
        scaler_enabled = bool(self.config.train.get("amp", False)) and torch.cuda.is_available()
        self._scaler = torch.amp.GradScaler("cuda", enabled=scaler_enabled)
        self._hook_runner = HookRunner()
        self._checkpoint_io = LocalCheckpointIO()

        self.model = None
        self.loss_module = None
        self.optimizer = None
        self.lr_scheduler = None
        self.train_loader = None
        self.val_loader = None
        self.global_step = 0
        self._tb_writer = None
        self._evaluator = None
        self._visualizer = None
        self._validation_report_writer = ValidationReportWriter()

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

    def _build_val_loader(self):
        validate_cfg = self.config.get("validate", {})
        if not bool(validate_cfg.get("enabled", False)):
            self.val_loader = None
            return

        if "val_dataset" in self.config and self.config.val_dataset is not None:
            val_dataset_cfg = self.config.val_dataset
        else:
            val_dataset_cfg = DictConfig(self.config.dataset.to_dict())
            val_dataset_cfg["train"] = False

        val_dataset = build_dataset(val_dataset_cfg.name, val_dataset_cfg, self.config)
        sampler = None
        if self.distributed:
            sampler = DistributedSampler(val_dataset,
                                         num_replicas=self.world_size,
                                         rank=self.rank,
                                         shuffle=False)
        collate_fn = getattr(val_dataset, "collate_fn", None)
        val_batch_size = int(
            val_dataset_cfg.get("batch_size", self.config.dataset.get("batch_size", 32)))
        self.val_loader = DataLoader(
            val_dataset,
            batch_size=val_batch_size,
            shuffle=False,
            sampler=sampler,
            num_workers=int(
                validate_cfg.get("num_workers", self.config.train.get("num_workers", 2))),
            collate_fn=collate_fn,
            drop_last=False,
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

    def _build_evaluator(self):
        validate_cfg = self.config.get("validate", {})
        if not bool(validate_cfg.get("enabled", False)):
            self._evaluator = None
            return
        if "evaluation" not in self.config or self.config.evaluation is None:
            raise ValueError(
                "Validation is enabled but 'evaluation.name' is missing in config.")
        self._evaluator = build_evaluator(self.config.evaluation.name, self.config.evaluation,
                                          self.config)

    def _build_visualizer(self):
        if "visualization" not in self.config or self.config.visualization is None:
            self._visualizer = None
            return
        self._visualizer = build_visualizer(self.config.visualization.name,
                                            self.config.visualization, self.config)

    def _setup_runtime(self):
        self._setup_seed(int(self.config.get("seed", 42)))
        if self.distributed:
            init_distributed()
            self.rank = get_rank()
            self.world_size = get_world_size()
            if torch.cuda.is_available():
                self.device = torch.device(f"cuda:{get_local_rank()}")
        self._build_train_loader()
        self._build_val_loader()
        self._build_model_and_loss()
        self._build_optimizer()
        self._build_evaluator()
        self._build_visualizer()
        self._setup_tensorboard()

        if self.rank == 0:
            logging.basicConfig(level=logging.INFO,
                                format="[%(asctime)s][%(levelname)s] %(message)s")

    def _setup_tensorboard(self):
        tb_cfg = self.config.get("tensorboard", {})
        if self.rank != 0 or not bool(tb_cfg.get("enabled", False)):
            self._tb_writer = None
            return
        log_dir = tb_cfg.get("log_dir")
        if not log_dir:
            output_dir = Path(self.config.train.get("output_dir", "outputs"))
            log_dir = str(output_dir / "tb")
        self._tb_writer = SummaryWriter(log_dir=log_dir)
        logger.info("TensorBoard logging to %s", log_dir)

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

    def _should_validate_by_step(self) -> bool:
        validate_cfg = self.config.get("validate", {})
        if not bool(validate_cfg.get("enabled", False)) or self.val_loader is None:
            return False
        interval = int(validate_cfg.get("val_interval_steps", 0))
        return interval > 0 and self.global_step > 0 and self.global_step % interval == 0

    def _should_validate_by_epoch(self, epoch: int) -> bool:
        validate_cfg = self.config.get("validate", {})
        if not bool(validate_cfg.get("enabled", False)) or self.val_loader is None:
            return False
        interval = int(validate_cfg.get("val_interval_epochs", 0))
        return interval > 0 and (epoch + 1) % interval == 0

    def _should_log_images(self) -> bool:
        tb_cfg = self.config.get("tensorboard", {})
        if self._tb_writer is None or not bool(tb_cfg.get("enabled", False)):
            return False
        interval = int(tb_cfg.get("image_interval_steps", 0))
        return interval > 0 and self.global_step > 0 and self.global_step % interval == 0

    def _validate_once(self, context: Dict[str, Any], trigger: str) -> Optional[Dict[str, float]]:
        if self.val_loader is None or self._evaluator is None:
            return None

        if self.distributed and isinstance(self.val_loader.sampler, DistributedSampler):
            self.val_loader.sampler.set_epoch(int(context.get("epoch", 0)))

        was_training = self.model.training
        self.model.eval()
        max_val_batches = int(self.config.get("validate", {}).get("max_val_batches", 0))
        should_log_images = self.rank == 0 and self._should_log_images()
        max_visualization_samples = int(self.config.get("tensorboard", {}).get(
            "num_visualization_samples", 16))
        initial_context = {
            "trigger": trigger,
            "epoch": int(context.get("epoch", 0)),
            "global_step": self.global_step,
            "device": self.device,
            "should_log_images": should_log_images,
            "max_visualization_samples": max_visualization_samples,
        }
        self._evaluator.reset(initial_context)

        with torch.no_grad():
            for batch_idx, batch in enumerate(self.val_loader):
                if max_val_batches > 0 and batch_idx >= max_val_batches:
                    break

                data_dict = normalize_batch_to_data_dict(batch)
                data_dict = to_device(data_dict, self.device)
                data_dict = self.model(data_dict)
                loss_dict = self._compute_loss(data_dict)
                data_dict["_loss_dict"] = loss_dict
                update_context = {
                    "trigger": trigger,
                    "epoch": int(context.get("epoch", 0)),
                    "global_step": self.global_step,
                    "val_batch_idx": batch_idx,
                }
                self._evaluator.update(data_dict, update_context)

        reduce_fn = ddp_all_reduce_sum if self.distributed else None
        result = self._evaluator.finalize(
            {
                "trigger": trigger,
                "epoch": int(context.get("epoch", 0)),
                "global_step": self.global_step,
            },
            reduce_fn=reduce_fn,
        )
        if self.rank == 0:
            visualizer_context = {
                "global_step": self.global_step,
                "should_log_images": should_log_images,
            }
            if self._tb_writer is not None and self._visualizer is not None:
                self._visualizer.log(result, visualizer_context, self._tb_writer)
            report_path = self._validation_report_writer.save(result, self.config)
            logger.info(
                "validate trigger=%s step=%d val_loss=%.6f val_accuracy=%.4f processed_val_batches=%d report=%s",
                trigger,
                self.global_step,
                float(result.metrics.get("val/loss", 0.0)),
                float(result.metrics.get("val/accuracy", 0.0)),
                int(result.meta.get("processed_val_batches", 0)),
                report_path,
            )

        if was_training:
            self.model.train()
        synchronize()
        return dict(result.metrics)

    def _train_one_batch(self, batch: Any, context: Dict[str, Any]) -> Optional[float]:
        data_dict = normalize_batch_to_data_dict(batch)
        data_dict = to_device(data_dict, self.device)
        data_dict = self._hook_runner.run_before_iteration(data_dict, context)

        self.optimizer.zero_grad(set_to_none=True)
        use_amp = bool(self.config.train.get("amp", False)) and self.device.type == "cuda"
        with torch.amp.autocast(device_type="cuda", enabled=use_amp):
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
        if self.rank == 0 and self._tb_writer is not None:
            self._tb_writer.add_scalar("train/total_loss", float(total_loss.detach().item()),
                                       self.global_step)
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
                    if self._should_validate_by_step():
                        self._validate_once(context, trigger="step")

                    if max_steps > 0 and self.global_step >= max_steps:
                        break

                synchronize()
                if self._should_validate_by_epoch(epoch):
                    epoch_context = {
                        "epoch": epoch,
                        "batch_idx": -1,
                        "global_step": self.global_step,
                        "rank": self.rank,
                    }
                    self._validate_once(epoch_context, trigger="epoch")
                if max_steps > 0 and self.global_step >= max_steps:
                    break
        finally:
            if self.rank == 0 and self._tb_writer is not None:
                self._tb_writer.flush()
                self._tb_writer.close()
            if self.distributed:
                cleanup_distributed()
