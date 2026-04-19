from typing import Any, Dict

import torch
import torch.nn.functional as F

from unified_train_pipeline.core.base_module import BaseModule, DataContract
from unified_train_pipeline.core.dict_config import DictConfig
from unified_train_pipeline.registry.module_register import MODULE_REGISTER


@MODULE_REGISTER.register_module()
class MnistMlpBackbone(BaseModule):

    def __init__(self, module_config: DictConfig, global_config: DictConfig):
        super().__init__(module_config, global_config)
        hidden_dim = int(module_config.get("hidden_dim", 256))
        num_classes = int(module_config.get("num_classes", 10))
        self.net = torch.nn.Sequential(
            torch.nn.Flatten(),
            torch.nn.Linear(28 * 28, hidden_dim),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden_dim, num_classes),
        )

    def _define_data_contract(self) -> DataContract:
        return DataContract(input_keys={"image": None},
                            output_keys={"logits": None})

    def _forward_impl(self, data_dict: Dict[str, Any]) -> Dict[str, Any]:
        data_dict["logits"] = self.net(data_dict["image"])
        return data_dict


@MODULE_REGISTER.register_module()
class MnistConvBackbone(BaseModule):

    def __init__(self, module_config: DictConfig, global_config: DictConfig):
        super().__init__(module_config, global_config)
        num_classes = int(module_config.get("num_classes", 10))
        self.features = torch.nn.Sequential(
            torch.nn.Conv2d(1, 32, kernel_size=3, padding=1),
            torch.nn.ReLU(),
            torch.nn.MaxPool2d(2),
            torch.nn.Conv2d(32, 64, kernel_size=3, padding=1),
            torch.nn.ReLU(),
            torch.nn.MaxPool2d(2),
        )
        self.classifier = torch.nn.Sequential(
            torch.nn.Flatten(),
            torch.nn.Linear(64 * 7 * 7, 128),
            torch.nn.ReLU(),
            torch.nn.Linear(128, num_classes),
        )

    def _define_data_contract(self) -> DataContract:
        return DataContract(input_keys={"image": None},
                            output_keys={"logits": None})

    def _forward_impl(self, data_dict: Dict[str, Any]) -> Dict[str, Any]:
        x = self.features(data_dict["image"])
        data_dict["logits"] = self.classifier(x)
        return data_dict


@MODULE_REGISTER.register_module()
class ClassificationCrossEntropyLoss(torch.nn.Module):
    """Compute classification cross entropy from data_dict."""

    def __init__(self, module_config: DictConfig, global_config: DictConfig):
        super().__init__()
        self._weight = float(module_config.get("weight", 1.0))

    def forward(self, data_dict: Dict[str, Any]) -> Dict[str, torch.Tensor]:
        loss = F.cross_entropy(data_dict["logits"], data_dict["label"])
        weighted = loss * self._weight
        return {"cls_loss": loss, "total_loss": weighted}
