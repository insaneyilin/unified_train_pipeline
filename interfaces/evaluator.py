from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

import torch


@dataclass
class EvaluationResult:
    metrics: Dict[str, float] = field(default_factory=dict)
    breakdowns: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)


class Evaluator(ABC):
    """Task-specific evaluator interface for validation."""

    def __init__(self, module_config: Any, global_config: Any):
        self.module_config = module_config
        self.global_config = global_config

    @abstractmethod
    def reset(self, context: Dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def update(self, data_dict: Dict[str, Any], context: Dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def finalize(
            self,
            context: Dict[str, Any],
            reduce_fn: Optional[Callable[[torch.Tensor], torch.Tensor]] = None
    ) -> EvaluationResult:
        raise NotImplementedError
