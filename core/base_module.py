from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set, Tuple

import torch

from unified_train_pipeline.core.dict_config import DictConfig


@dataclass
class DataContract:
    """Input/output key contract for a module."""

    input_keys: Dict[str, Optional[Tuple[int, ...]]]
    output_keys: Dict[str, Optional[Tuple[int, ...]]]
    optional_input_keys: Set[str] = field(default_factory=set)
    optional_output_keys: Set[str] = field(default_factory=set)


class DataDictValidator:
    """Validate a runtime data_dict against a contract."""

    @staticmethod
    def _validate_shape(tensor: torch.Tensor, expected_shape: Optional[Tuple[int,
                                                                            ...]],
                        key: str, module_name: str, is_input: bool) -> None:
        if expected_shape is None:
            return

        if len(tensor.shape) != len(expected_shape):
            direction = "input" if is_input else "output"
            raise ValueError(
                f"Module {module_name} expects {direction} '{key}' to have "
                f"{len(expected_shape)} dims, but got {len(tensor.shape)} "
                f"(expected={expected_shape}, got={tuple(tensor.shape)})")

        for i, (expected_dim, actual_dim) in enumerate(
                zip(expected_shape, tensor.shape)):
            if expected_dim is not None and expected_dim != actual_dim:
                direction = "input" if is_input else "output"
                raise ValueError(
                    f"Module {module_name} expects {direction} '{key}' dim {i} "
                    f"to be {expected_dim}, but got {actual_dim}.")

    @staticmethod
    def validate_input(module_name: str, data_dict: Dict[str, Any],
                       data_contract: DataContract) -> None:
        for key, expected_shape in data_contract.input_keys.items():
            if key not in data_dict:
                if key in data_contract.optional_input_keys:
                    continue
                raise ValueError(
                    f"Module {module_name} requires input key '{key}' but it is missing."
                )
            value = data_dict[key]
            if isinstance(value, torch.Tensor):
                DataDictValidator._validate_shape(value, expected_shape, key,
                                                  module_name, True)
            elif expected_shape is not None:
                raise ValueError(
                    f"Module {module_name} expects input '{key}' as Tensor with shape {expected_shape}, "
                    f"but got {type(value).__name__}.")

    @staticmethod
    def validate_output(module_name: str, data_dict: Dict[str, Any],
                        data_contract: DataContract) -> None:
        for key, expected_shape in data_contract.output_keys.items():
            if key not in data_dict:
                if key in data_contract.optional_output_keys:
                    continue
                raise ValueError(
                    f"Module {module_name} requires output key '{key}' but it is missing."
                )
            value = data_dict[key]
            if isinstance(value, torch.Tensor):
                DataDictValidator._validate_shape(value, expected_shape, key,
                                                  module_name, False)
            elif expected_shape is not None:
                raise ValueError(
                    f"Module {module_name} expects output '{key}' as Tensor with shape {expected_shape}, "
                    f"but got {type(value).__name__}.")


class BaseModule(torch.nn.Module, ABC):
    """Base module with config access and data contract validation."""

    def __init__(self, module_config: DictConfig, global_config: DictConfig,
                 **kwargs):
        super().__init__(**kwargs)
        self._setup_config(module_config, global_config)
        self._is_inference_mode = False

    def _setup_config(self, module_config: DictConfig, global_config: DictConfig):
        self._module_config = module_config
        self._global_config = global_config
        self._data_contract = None
        if module_config:
            assert "name" in module_config, (
                f"Module {self.__class__.__name__} config must include 'name'")
            if module_config.name != self.__class__.__name__:
                raise ValueError(
                    f"Config name must match class name for {self.__class__.__name__}, "
                    f"got {module_config.name}")

    @property
    def is_inference_mode(self) -> bool:
        return self._is_inference_mode

    @is_inference_mode.setter
    def is_inference_mode(self, value: bool) -> None:
        self._is_inference_mode = value

    @property
    def data_contract(self) -> DataContract:
        if self._data_contract is None:
            self._data_contract = self._define_data_contract()
            if not isinstance(self._data_contract, DataContract):
                raise ValueError(
                    f"{self.__class__.__name__}._define_data_contract() must return DataContract"
                )
        return self._data_contract

    @abstractmethod
    def _define_data_contract(self) -> DataContract:
        raise NotImplementedError

    @abstractmethod
    def _forward_impl(self, data_dict: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def forward(self, data_dict: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data_dict, dict):
            raise ValueError(
                f"Module {self.__class__.__name__} expects dict, got {type(data_dict).__name__}"
            )
        contract = self.data_contract
        DataDictValidator.validate_input(self.__class__.__name__, data_dict,
                                         contract)
        result = self._forward_impl(data_dict)
        if not isinstance(result, dict):
            raise ValueError(
                f"Module {self.__class__.__name__} must return dict, got {type(result).__name__}"
            )
        DataDictValidator.validate_output(self.__class__.__name__, result,
                                          contract)
        return result

    def _get_config_param(self, param_name: str, default: Any = None) -> Any:
        if not self._module_config:
            return default
        try:
            value = self._module_config
            for key in param_name.split("."):
                if key not in value:
                    return default
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def _get_global_config_param(self,
                                 param_name: str,
                                 default: Any = None) -> Any:
        if not self._global_config:
            return default
        try:
            value = self._global_config
            for key in param_name.split("."):
                if key not in value:
                    return default
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def is_frozen(self) -> bool:
        if not self._module_config:
            return False
        return self._module_config.get("is_frozen", False)
