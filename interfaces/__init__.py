"""Extension interfaces for artifacts and prediction formatting."""

from unified_train_pipeline.interfaces.checkpoint_io import (CheckpointIO,
                                                             LocalCheckpointIO)
from unified_train_pipeline.interfaces.predict_formatter import PredictFormatter

__all__ = ["CheckpointIO", "LocalCheckpointIO", "PredictFormatter"]

