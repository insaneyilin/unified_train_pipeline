from abc import abstractmethod
from typing import Any, Dict

import torch

from unified_train_pipeline.core.base_module import BaseModule, DataContract
from unified_train_pipeline.core.dict_config import DictConfig


class BaseLossModule(BaseModule):
    """Base class for loss modules that update a shared loss_dict."""

    def __init__(self, module_config: DictConfig, global_config: DictConfig):
        super().__init__(module_config, global_config)
        self._weight = self._get_config_param("weight", 1.0)

    def _define_data_contract(self) -> DataContract:
        return DataContract(input_keys={}, output_keys={})

    def forward(self, data_dict: Dict[str, Any],
                loss_dict: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        return self._forward_impl(data_dict, loss_dict)

    @abstractmethod
    def _forward_impl(self, data_dict: Dict[str, Any],
                      loss_dict: Dict[str, torch.Tensor]) -> Dict[str,
                                                                    torch.Tensor]:
        raise NotImplementedError
