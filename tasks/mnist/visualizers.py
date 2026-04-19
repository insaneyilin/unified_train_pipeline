from typing import Any, Dict

import torch

from unified_train_pipeline.core.dict_config import DictConfig
from unified_train_pipeline.interfaces.evaluator import EvaluationResult
from unified_train_pipeline.interfaces.visualizer import Visualizer
from unified_train_pipeline.registry.visualizer_register import VISUALIZER_REGISTER
from unified_train_pipeline.train.tensorboard_utils import render_confusion_matrix_image


@VISUALIZER_REGISTER.register_visualizer()
class MnistTensorBoardVisualizer(Visualizer):
    """TensorBoard visualizer for MNIST validation outputs."""

    def __init__(self, module_config: DictConfig, global_config: DictConfig):
        super().__init__(module_config, global_config)
        self._tb_cfg = global_config.get("tensorboard", {})
        self._image_bucket_cfg = self._tb_cfg.get("image_buckets", {})

    def _get_bucket_flags(self) -> Dict[str, bool]:
        return {
            "random": bool(self._image_bucket_cfg.get("random", True)),
            "digit": bool(self._image_bucket_cfg.get("digit", True)),
            "pred_outcome": bool(self._image_bucket_cfg.get("pred_outcome", True)),
        }

    def _log_digit_breakdown_scalars(self, result: EvaluationResult, writer: Any,
                                     global_step: int) -> None:
        digit_total_counts = result.artifacts.get("digit_total_counts")
        digit_correct_counts = result.artifacts.get("digit_correct_counts")
        if not isinstance(digit_total_counts,
                          torch.Tensor) or not isinstance(digit_correct_counts, torch.Tensor):
            return
        num_classes = min(int(digit_total_counts.numel()), int(digit_correct_counts.numel()))
        for digit in range(num_classes):
            total = float(digit_total_counts[digit].item())
            correct = float(digit_correct_counts[digit].item())
            accuracy = (correct / total) if total > 0 else 0.0
            writer.add_scalar(f"val/digit/{digit}/accuracy", accuracy, global_step)
            writer.add_scalar(f"val/digit/{digit}/count", total, global_step)

    def _log_confusion_matrix(self, result: EvaluationResult, writer: Any,
                              global_step: int) -> None:
        confusion_matrix = result.artifacts.get("confusion_matrix")
        if not isinstance(confusion_matrix, torch.Tensor):
            return
        raw_image = render_confusion_matrix_image(confusion_matrix, normalize_rows=False)
        row_norm_image = render_confusion_matrix_image(confusion_matrix, normalize_rows=True)
        writer.add_image("val/confusion_matrix/raw", raw_image, global_step)
        writer.add_image("val/confusion_matrix/row_normalized", row_norm_image, global_step)

    def _log_validation_samples(self, result: EvaluationResult, writer: Any,
                                global_step: int) -> None:
        sampled_items = result.artifacts.get("sampled_items", [])
        if not sampled_items:
            return
        flags = self._get_bucket_flags()
        for item in sampled_items:
            image = item["image"]
            label = item["label"]
            pred = item["pred"]
            sample_id = item["sample_id"]
            outcome = "correct" if label == pred else "wrong"
            suffix = f"{sample_id}_gt_{label}_pred_{pred}"

            if flags["random"]:
                writer.add_image(f"val/random/{outcome}/{suffix}", image, global_step)
            if flags["digit"]:
                writer.add_image(f"val/digit/{label}/{outcome}/{suffix}", image,
                                 global_step)
            if flags["pred_outcome"]:
                pred_bucket = "pred_correct" if label == pred else "pred_wrong"
                writer.add_image(f"val/{pred_bucket}/{suffix}", image, global_step)

    def log(self, result: EvaluationResult, context: Dict[str, Any], writer: Any) -> None:
        if writer is None:
            return
        global_step = int(context.get("global_step", result.meta.get("global_step", 0)))

        for metric_name, metric_value in result.metrics.items():
            writer.add_scalar(metric_name, float(metric_value), global_step)
        self._log_digit_breakdown_scalars(result, writer, global_step)
        self._log_confusion_matrix(result, writer, global_step)
        if bool(context.get("should_log_images", False)):
            self._log_validation_samples(result, writer, global_step)
