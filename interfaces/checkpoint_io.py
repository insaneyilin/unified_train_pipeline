from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

import torch


class CheckpointIO(ABC):

    @abstractmethod
    def save(self, checkpoint: Dict[str, Any], path: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def load(self, path: str, map_location: str = "cpu") -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def exists(self, path: str) -> bool:
        raise NotImplementedError


class LocalCheckpointIO(CheckpointIO):
    """Local filesystem checkpoint backend."""

    def save(self, checkpoint: Dict[str, Any], path: str) -> None:
        save_path = Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(checkpoint, save_path)

    def load(self, path: str, map_location: str = "cpu") -> Dict[str, Any]:
        return torch.load(path, map_location=map_location)

    def exists(self, path: str) -> bool:
        return Path(path).exists()
