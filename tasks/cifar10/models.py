from typing import Any, Dict

import torch
from torchvision import models

from unified_train_pipeline.core.base_module import BaseModule, DataContract
from unified_train_pipeline.core.dict_config import DictConfig
from unified_train_pipeline.registry.module_register import MODULE_REGISTER


class _ResidualBlock(torch.nn.Module):

    def __init__(self, channels: int):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Conv2d(channels, channels, 3, padding=1, bias=False),
            torch.nn.BatchNorm2d(channels),
            torch.nn.ReLU(inplace=True),
            torch.nn.Conv2d(channels, channels, 3, padding=1, bias=False),
            torch.nn.BatchNorm2d(channels),
        )

    def forward(self, x):
        return torch.relu(self.net(x) + x)


@MODULE_REGISTER.register_module()
class CifarResNetBackbone(BaseModule):

    def __init__(self, module_config: DictConfig, global_config: DictConfig):
        super().__init__(module_config, global_config)
        num_classes = int(module_config.get("num_classes", 10))
        self.net = models.resnet18(weights=None, num_classes=num_classes)

    def _define_data_contract(self) -> DataContract:
        return DataContract(input_keys={"image": None},
                            output_keys={"logits": None})

    def _forward_impl(self, data_dict: Dict[str, Any]) -> Dict[str, Any]:
        data_dict["logits"] = self.net(data_dict["image"])
        return data_dict


@MODULE_REGISTER.register_module()
class CifarWideResNetBackbone(BaseModule):
    """Lightweight wide residual network for CIFAR-like inputs."""

    def __init__(self, module_config: DictConfig, global_config: DictConfig):
        super().__init__(module_config, global_config)
        width = int(module_config.get("width", 96))
        num_classes = int(module_config.get("num_classes", 10))
        self.stem = torch.nn.Sequential(
            torch.nn.Conv2d(3, width, kernel_size=3, padding=1, bias=False),
            torch.nn.BatchNorm2d(width),
            torch.nn.ReLU(inplace=True),
        )
        self.blocks = torch.nn.Sequential(
            _ResidualBlock(width),
            _ResidualBlock(width),
            _ResidualBlock(width),
            torch.nn.MaxPool2d(2),
            torch.nn.Conv2d(width, width * 2, 3, padding=1, bias=False),
            torch.nn.BatchNorm2d(width * 2),
            torch.nn.ReLU(inplace=True),
            _ResidualBlock(width * 2),
            torch.nn.AdaptiveAvgPool2d(1),
        )
        self.head = torch.nn.Linear(width * 2, num_classes)

    def _define_data_contract(self) -> DataContract:
        return DataContract(input_keys={"image": None},
                            output_keys={"logits": None})

    def _forward_impl(self, data_dict: Dict[str, Any]) -> Dict[str, Any]:
        x = self.stem(data_dict["image"])
        x = self.blocks(x)
        x = torch.flatten(x, 1)
        data_dict["logits"] = self.head(x)
        return data_dict
