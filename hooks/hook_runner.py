from typing import Any, Dict, Iterable


class HookRunner:
    """Run hook chains for each training phase."""

    def __init__(self,
                 before_iteration_hooks: Iterable = None,
                 after_forward_hooks: Iterable = None,
                 after_step_hooks: Iterable = None):
        self._before_iteration_hooks = list(before_iteration_hooks or [])
        self._after_forward_hooks = list(after_forward_hooks or [])
        self._after_step_hooks = list(after_step_hooks or [])

    def run_before_iteration(self, data_dict: Dict[str, Any],
                             context: Dict[str, Any]) -> Dict[str, Any]:
        for hook in self._before_iteration_hooks:
            data_dict = hook(data_dict, context)
        return data_dict

    def run_after_forward(self, data_dict: Dict[str, Any],
                          context: Dict[str, Any]) -> Dict[str, Any]:
        for hook in self._after_forward_hooks:
            data_dict = hook(data_dict, context)
        return data_dict

    def run_after_step(self, data_dict: Dict[str, Any],
                       context: Dict[str, Any]) -> Dict[str, Any]:
        for hook in self._after_step_hooks:
            data_dict = hook(data_dict, context)
        return data_dict
