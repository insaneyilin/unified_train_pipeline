from typing import Any, Dict

import torch


def to_device(batch: Dict[str, Any], device: torch.device) -> Dict[str, Any]:
    """Move nested tensors in dict/list to the target device."""

    def _move(value):
        if isinstance(value, torch.Tensor):
            return value.to(device)
        if isinstance(value, dict):
            return {k: _move(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_move(v) for v in value]
        return value

    return {k: _move(v) for k, v in batch.items()}


def normalize_batch_to_data_dict(batch: Any) -> Dict[str, Any]:
    """Convert common dataloader outputs into runtime data_dict."""
    if isinstance(batch, dict):
        return dict(batch)
    if isinstance(batch, (list, tuple)) and len(batch) == 2:
        return {"image": batch[0], "label": batch[1]}
    raise ValueError(
        "Unsupported batch structure. Expected dict or tuple(image, label).")
