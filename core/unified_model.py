from typing import Any, Dict

import torch

from unified_train_pipeline.core.base_module import BaseModule, DataContract
from unified_train_pipeline.core.dict_config import DictConfig
from unified_train_pipeline.registry.module_register import (MODULE_REGISTER,
                                                             build_module)


@MODULE_REGISTER.register_module()
class UnifiedModel(BaseModule):
    """Execute configured submodules sequentially over one shared data_dict."""

    def __init__(self, module_config: DictConfig, global_config: DictConfig):
        super().__init__(module_config, global_config)
        assert "submodules" in module_config, (
            "UnifiedModel config must include 'submodules'")
        self._submodules = torch.nn.ModuleDict({
            submodule_key:
            build_module(submodule_config.name, submodule_config, global_config)
            for submodule_key, submodule_config in module_config.submodules.items()
        })

        self.is_inference_mode = self._get_config_param("is_inference_mode",
                                                        False)
        if self.is_inference_mode:
            for submodule in self._submodules.values():
                if isinstance(submodule, BaseModule):
                    submodule.is_inference_mode = True

    def _define_data_contract(self) -> DataContract:
        # UnifiedModel intentionally keeps a broad contract.
        return DataContract(input_keys={}, output_keys={})

    def _forward_impl(self, data_dict: Dict[str, Any]) -> Dict[str, Any]:
        for submodule in self._submodules.values():
            data_dict = submodule(data_dict)
        return data_dict
