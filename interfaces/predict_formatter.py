from abc import ABC, abstractmethod
from typing import Any, Dict


class PredictFormatter(ABC):
    """Optional prediction formatting interface for task-specific outputs."""

    @abstractmethod
    def format(self, data_dict: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
