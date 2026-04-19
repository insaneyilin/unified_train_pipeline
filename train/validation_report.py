import json
from pathlib import Path
from typing import Any, Dict

import torch

from unified_train_pipeline.interfaces.evaluator import EvaluationResult


class ValidationReportWriter:
    """Persist validation outputs as JSON reports."""

    def _build_val_id(self, result: EvaluationResult, config: Any) -> str:
        validate_cfg = config.get("validate", {})
        trigger = str(result.meta.get("trigger", "unknown"))
        epoch = int(result.meta.get("epoch", 0))
        global_step = int(result.meta.get("global_step", 0))
        processed_batches = int(result.meta.get("processed_val_batches", 0))
        step_interval = int(validate_cfg.get("val_interval_steps", 0))
        epoch_interval = int(validate_cfg.get("val_interval_epochs", 0))
        max_val_batches = int(validate_cfg.get("max_val_batches", 0))
        max_batches_tag = str(max_val_batches) if max_val_batches > 0 else "all"
        return (
            f"trigger-{trigger}_epoch-{epoch:03d}_step-{global_step:06d}_"
            f"stepint-{step_interval}_epochint-{epoch_interval}_"
            f"maxvb-{max_batches_tag}_runvb-{processed_batches}")

    def _build_confusion_payload(self, result: EvaluationResult) -> Dict[str, Any]:
        confusion_matrix = result.artifacts.get("confusion_matrix")
        if not isinstance(confusion_matrix, torch.Tensor):
            return {}

        confusion_raw = confusion_matrix.to(torch.int64).tolist()
        confusion_row_normalized = []
        for row in confusion_raw:
            row_sum = sum(row)
            if row_sum > 0:
                confusion_row_normalized.append([float(v / row_sum) for v in row])
            else:
                confusion_row_normalized.append([0.0 for _ in row])
        return {
            "raw": confusion_raw,
            "row_normalized": confusion_row_normalized,
        }

    def save(self, result: EvaluationResult, config: Any) -> Path:
        output_dir = Path(config.train.get("output_dir", "outputs"))
        report_dir = output_dir / "val_metrics"
        report_dir.mkdir(parents=True, exist_ok=True)

        val_id = self._build_val_id(result, config)
        report_path = report_dir / f"val_metrics-{val_id}.json"
        report_payload = {
            "val_id": val_id,
            "trigger": result.meta.get("trigger"),
            "epoch": int(result.meta.get("epoch", 0)),
            "global_step": int(result.meta.get("global_step", 0)),
            "validate_config": {
                "val_interval_steps": int(config.get("validate", {}).get(
                    "val_interval_steps", 0)),
                "val_interval_epochs": int(config.get("validate", {}).get(
                    "val_interval_epochs", 0)),
                "max_val_batches": int(config.get("validate", {}).get("max_val_batches", 0)),
                "processed_val_batches": int(result.meta.get("processed_val_batches", 0)),
            },
            "metrics": {k: float(v)
                        for k, v in result.metrics.items()},
            "breakdown": result.breakdowns,
        }
        confusion_payload = self._build_confusion_payload(result)
        if confusion_payload:
            report_payload["confusion_matrix"] = confusion_payload

        with report_path.open("w", encoding="utf-8") as f:
            json.dump(report_payload, f, indent=2)
        return report_path
