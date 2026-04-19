import random
from typing import Any, Callable, Dict, Optional

import torch

from unified_train_pipeline.core.dict_config import DictConfig
from unified_train_pipeline.interfaces.evaluator import EvaluationResult, Evaluator
from unified_train_pipeline.registry.evaluator_register import EVALUATOR_REGISTER
from unified_train_pipeline.train.tensorboard_utils import to_float_image_batch


@EVALUATOR_REGISTER.register_evaluator()
class MnistClassificationEvaluator(Evaluator):
    """MNIST classification evaluator with metric and sample aggregation."""

    def __init__(self, module_config: DictConfig, global_config: DictConfig):
        super().__init__(module_config, global_config)
        self._num_classes = int(module_config.get("num_classes", 10))
        self._max_visualization_samples = 0
        self._should_collect_samples = False
        self._device = torch.device("cpu")
        self._loss_sum = None
        self._loss_weight = None
        self._correct_sum = None
        self._count_sum = None
        self._digit_total_counts = None
        self._digit_correct_counts = None
        self._confusion_matrix = None
        self._sampled_items = []
        self._seen_items = 0
        self._processed_batches = 0

    def reset(self, context: Dict[str, Any]) -> None:
        self._device = context.get("device", torch.device("cpu"))
        self._should_collect_samples = bool(context.get("should_log_images", False))
        self._max_visualization_samples = int(context.get("max_visualization_samples", 0))
        self._loss_sum = torch.zeros(1, device=self._device, dtype=torch.float32)
        self._loss_weight = torch.zeros(1, device=self._device, dtype=torch.float32)
        self._correct_sum = torch.zeros(1, device=self._device, dtype=torch.float32)
        self._count_sum = torch.zeros(1, device=self._device, dtype=torch.float32)
        self._digit_total_counts = torch.zeros(self._num_classes,
                                               device=self._device,
                                               dtype=torch.float32)
        self._digit_correct_counts = torch.zeros(self._num_classes,
                                                 device=self._device,
                                                 dtype=torch.float32)
        self._confusion_matrix = torch.zeros((self._num_classes, self._num_classes),
                                             device=self._device,
                                             dtype=torch.float32)
        self._sampled_items = []
        self._seen_items = 0
        self._processed_batches = 0

    def _sample_should_replace(self, seen_count: int, keep_size: int) -> bool:
        if seen_count <= keep_size:
            return True
        return random.randint(1, seen_count) <= keep_size

    def _format_sample_id(self, context: Dict[str, Any], val_batch_idx: int,
                          sample_idx: int) -> str:
        epoch = int(context.get("epoch", 0))
        global_step = int(context.get("global_step", 0))
        return (
            f"e{epoch:03d}_st{global_step:06d}_vb{val_batch_idx:04d}_"
            f"s{sample_idx:03d}")

    def update(self, data_dict: Dict[str, Any], context: Dict[str, Any]) -> None:
        labels = data_dict.get("label")
        logits = data_dict.get("logits")
        if not isinstance(labels, torch.Tensor) or not isinstance(logits, torch.Tensor):
            raise ValueError(
                "MnistClassificationEvaluator requires tensor 'label' and 'logits'.")
        loss_dict = data_dict.get("_loss_dict")
        if not isinstance(loss_dict, dict) or "total_loss" not in loss_dict:
            raise ValueError("MnistClassificationEvaluator requires '_loss_dict.total_loss'.")

        batch_loss = loss_dict["total_loss"].detach().to(dtype=torch.float32)
        batch_weight = float(labels.shape[0])
        self._loss_sum += batch_loss * batch_weight
        self._loss_weight += batch_weight
        self._processed_batches += 1

        preds = torch.argmax(logits, dim=1)
        self._correct_sum += (preds == labels).to(torch.float32).sum()
        self._count_sum += float(labels.numel())

        label_counts = torch.bincount(labels.to(torch.int64), minlength=self._num_classes)
        correct_counts = torch.bincount(labels[preds == labels].to(torch.int64),
                                        minlength=self._num_classes)
        self._digit_total_counts += label_counts.to(dtype=torch.float32)
        self._digit_correct_counts += correct_counts.to(dtype=torch.float32)

        pair_indices = labels.to(torch.int64) * self._num_classes + preds.to(torch.int64)
        pair_counts = torch.bincount(pair_indices,
                                     minlength=self._num_classes * self._num_classes).reshape(
                                         self._num_classes, self._num_classes)
        self._confusion_matrix += pair_counts.to(dtype=torch.float32)

        if self._should_collect_samples and self._max_visualization_samples > 0 and isinstance(
                data_dict.get("image"), torch.Tensor):
            image_batch = to_float_image_batch(data_dict["image"])
            label_batch = labels.detach().cpu()
            pred_batch = preds.detach().cpu()
            row_count = min(image_batch.shape[0], label_batch.shape[0], pred_batch.shape[0])
            for sample_idx in range(row_count):
                self._seen_items += 1
                current_item = {
                    "image": image_batch[sample_idx],
                    "label": int(label_batch[sample_idx].item()),
                    "pred": int(pred_batch[sample_idx].item()),
                    "sample_id": self._format_sample_id(
                        context,
                        val_batch_idx=int(context.get("val_batch_idx", 0)),
                        sample_idx=sample_idx,
                    ),
                }
                if len(self._sampled_items) < self._max_visualization_samples:
                    self._sampled_items.append(current_item)
                elif self._sample_should_replace(self._seen_items,
                                                 self._max_visualization_samples):
                    replace_idx = random.randint(0, self._max_visualization_samples - 1)
                    self._sampled_items[replace_idx] = current_item

    def finalize(
            self,
            context: Dict[str, Any],
            reduce_fn: Optional[Callable[[torch.Tensor], torch.Tensor]] = None
    ) -> EvaluationResult:
        if reduce_fn is not None:
            self._loss_sum = reduce_fn(self._loss_sum)
            self._loss_weight = reduce_fn(self._loss_weight)
            self._correct_sum = reduce_fn(self._correct_sum)
            self._count_sum = reduce_fn(self._count_sum)
            self._digit_total_counts = reduce_fn(self._digit_total_counts)
            self._digit_correct_counts = reduce_fn(self._digit_correct_counts)
            self._confusion_matrix = reduce_fn(self._confusion_matrix)

        loss_weight = float(self._loss_weight.item())
        count_sum = float(self._count_sum.item())
        val_loss = float(self._loss_sum.item() / loss_weight) if loss_weight > 0 else 0.0
        val_accuracy = float(
            self._correct_sum.item() / count_sum) if count_sum > 0 else 0.0

        digit_breakdown = {}
        for digit in range(self._num_classes):
            total = float(self._digit_total_counts[digit].item())
            correct = float(self._digit_correct_counts[digit].item())
            digit_breakdown[str(digit)] = {
                "count": int(total),
                "correct": int(correct),
                "accuracy": (correct / total) if total > 0 else 0.0,
            }

        return EvaluationResult(
            metrics={
                "val/loss": val_loss,
                "val/accuracy": val_accuracy,
            },
            breakdowns={
                "digit": digit_breakdown,
            },
            artifacts={
                "digit_total_counts": self._digit_total_counts.detach().cpu(),
                "digit_correct_counts": self._digit_correct_counts.detach().cpu(),
                "confusion_matrix": self._confusion_matrix.detach().cpu(),
                "sampled_items": list(self._sampled_items),
            },
            meta={
                "trigger": context.get("trigger"),
                "epoch": int(context.get("epoch", 0)),
                "global_step": int(context.get("global_step", 0)),
                "processed_val_batches": self._processed_batches,
                "num_classes": self._num_classes,
            },
        )
