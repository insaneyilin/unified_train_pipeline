from typing import Any, Dict, List

import torch
from torchvision.models.detection import (fasterrcnn_resnet50_fpn,
                                          retinanet_resnet50_fpn)

from unified_train_pipeline.core.base_module import BaseModule, DataContract
from unified_train_pipeline.core.dict_config import DictConfig
from unified_train_pipeline.registry.module_register import MODULE_REGISTER


def _normalize_images(images: Any) -> List[torch.Tensor]:
    if isinstance(images, torch.Tensor):
        return [img for img in images]
    if isinstance(images, list):
        return images
    raise ValueError("Detection model expects image as tensor batch or list.")


@MODULE_REGISTER.register_module()
class CocoFasterRCNNDetector(BaseModule):

    def __init__(self, module_config: DictConfig, global_config: DictConfig):
        super().__init__(module_config, global_config)
        num_classes = int(module_config.get("num_classes", 81))
        self.detector = fasterrcnn_resnet50_fpn(weights=None,
                                                weights_backbone=None,
                                                num_classes=num_classes)

    def _define_data_contract(self) -> DataContract:
        return DataContract(input_keys={"image": None, "targets": None},
                            output_keys={"detector_loss_dict": None,
                                         "total_loss": None},
                            optional_output_keys={"detections"})

    def _forward_impl(self, data_dict: Dict[str, Any]) -> Dict[str, Any]:
        images = _normalize_images(data_dict["image"])
        targets = data_dict.get("targets", None)
        if self.training:
            loss_dict = self.detector(images, targets)
            total_loss = sum(loss_dict.values())
            data_dict["detector_loss_dict"] = loss_dict
            data_dict["total_loss"] = total_loss
        else:
            data_dict["detections"] = self.detector(images)
            data_dict["detector_loss_dict"] = {}
            data_dict["total_loss"] = torch.tensor(0.0, device=images[0].device)
        return data_dict


@MODULE_REGISTER.register_module()
class CocoRetinaNetDetector(BaseModule):

    def __init__(self, module_config: DictConfig, global_config: DictConfig):
        super().__init__(module_config, global_config)
        num_classes = int(module_config.get("num_classes", 81))
        self.detector = retinanet_resnet50_fpn(weights=None,
                                               weights_backbone=None,
                                               num_classes=num_classes)

    def _define_data_contract(self) -> DataContract:
        return DataContract(input_keys={"image": None, "targets": None},
                            output_keys={"detector_loss_dict": None,
                                         "total_loss": None},
                            optional_output_keys={"detections"})

    def _forward_impl(self, data_dict: Dict[str, Any]) -> Dict[str, Any]:
        images = _normalize_images(data_dict["image"])
        targets = data_dict.get("targets", None)
        if self.training:
            loss_dict = self.detector(images, targets)
            total_loss = sum(loss_dict.values())
            data_dict["detector_loss_dict"] = loss_dict
            data_dict["total_loss"] = total_loss
        else:
            data_dict["detections"] = self.detector(images)
            data_dict["detector_loss_dict"] = {}
            data_dict["total_loss"] = torch.tensor(0.0, device=images[0].device)
        return data_dict


@MODULE_REGISTER.register_module()
class DetectionLossFromDataDict(torch.nn.Module):
    """Expose detector losses to the generic trainer interface."""

    def __init__(self, module_config: DictConfig, global_config: DictConfig):
        super().__init__()
        self._weight = float(module_config.get("weight", 1.0))

    def forward(self, data_dict: Dict[str, Any]) -> Dict[str, torch.Tensor]:
        loss_dict = data_dict.get("detector_loss_dict", {})
        total_loss = data_dict["total_loss"] * self._weight
        output = {"total_loss": total_loss}
        for key, value in loss_dict.items():
            output[str(key)] = value
        return output
