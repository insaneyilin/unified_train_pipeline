from abc import ABC, abstractmethod
from typing import Any, Dict

from unified_train_pipeline.interfaces.evaluator import EvaluationResult


class Visualizer(ABC):
    """Task-specific visualization interface for validation outputs."""

    def __init__(self, module_config: Any, global_config: Any):
        self.module_config = module_config
        self.global_config = global_config

    @abstractmethod
    def log(self, result: EvaluationResult, context: Dict[str, Any],
            writer: Any) -> None:
        raise NotImplementedError
