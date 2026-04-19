import time
from typing import Any, Dict


class IterationTimerHook:
    """Track iteration elapsed time in context."""

    def __call__(self, data_dict: Dict[str, Any], context: Dict[str,
                                                                Any]) -> Dict[str,
                                                                              Any]:
        context["iter_start_time"] = time.time()
        return data_dict


class LossDetachHook:
    """Store detached scalar loss for logging."""

    def __call__(self, data_dict: Dict[str, Any], context: Dict[str,
                                                                Any]) -> Dict[str,
                                                                              Any]:
        loss_dict = data_dict.get("_loss_dict", {})
        if "total_loss" in loss_dict:
            context["last_total_loss"] = float(loss_dict["total_loss"].detach().item())
        return data_dict
