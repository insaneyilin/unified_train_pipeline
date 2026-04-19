from pathlib import Path
from typing import Any, Dict, List

import torch
from PIL import Image
from torchvision import datasets, transforms

from unified_train_pipeline.core.dict_config import DictConfig
from unified_train_pipeline.registry.dataset_register import DATASET_REGISTER


class _SyntheticCocoLikeDataset(torch.utils.data.Dataset):
    """Fallback synthetic dataset when real COCO128 files are unavailable."""

    def __init__(self, length: int = 32, image_size: int = 320):
        self.length = length
        self.image_size = image_size

    def __len__(self):
        return self.length

    def __getitem__(self, idx: int):
        image = torch.rand(3, self.image_size, self.image_size)
        num_boxes = 2
        boxes = torch.tensor([[20, 20, 120, 120], [80, 80, 200, 220]],
                             dtype=torch.float32)
        labels = torch.tensor([1, 2], dtype=torch.int64)
        target = {
            "boxes": boxes,
            "labels": labels,
            "image_id": torch.tensor([idx], dtype=torch.int64),
            "area": (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1]),
            "iscrowd": torch.zeros((num_boxes, ), dtype=torch.int64),
        }
        return {"image": image, "targets": target}


@DATASET_REGISTER.register_dataset()
class Coco128DetectionDataset(torch.utils.data.Dataset):
    """COCO-style detection dataset wrapper with synthetic fallback."""

    def __init__(self, module_config: DictConfig, global_config: DictConfig):
        root = Path(module_config.get("root", "./data/coco128/images/train2017"))
        ann_file = Path(
            module_config.get("ann_file",
                              "./data/coco128/annotations/instances_train2017.json"))
        self._image_transform = transforms.ToTensor()
        self._use_real = root.exists() and ann_file.exists()
        if self._use_real:
            self._dataset = datasets.CocoDetection(root=str(root),
                                                   annFile=str(ann_file))
        else:
            self._dataset = _SyntheticCocoLikeDataset(
                length=int(module_config.get("synthetic_length", 32)),
                image_size=int(module_config.get("image_size", 320)),
            )

    def __len__(self):
        return len(self._dataset)

    @staticmethod
    def collate_fn(batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        images = [item["image"] for item in batch]
        targets = [item["targets"] for item in batch]
        return {"image": images, "targets": targets}

    def _convert_target(self, raw_target: List[Dict[str, Any]],
                        image_id: int) -> Dict[str, torch.Tensor]:
        boxes = []
        labels = []
        area = []
        iscrowd = []
        for ann in raw_target:
            if "bbox" not in ann:
                continue
            x, y, w, h = ann["bbox"]
            if w <= 1 or h <= 1:
                continue
            boxes.append([x, y, x + w, y + h])
            labels.append(int(ann.get("category_id", 1)))
            area.append(float(ann.get("area", w * h)))
            iscrowd.append(int(ann.get("iscrowd", 0)))

        if len(boxes) == 0:
            boxes = torch.zeros((0, 4), dtype=torch.float32)
            labels = torch.zeros((0, ), dtype=torch.int64)
            area = torch.zeros((0, ), dtype=torch.float32)
            iscrowd = torch.zeros((0, ), dtype=torch.int64)
        else:
            boxes = torch.tensor(boxes, dtype=torch.float32)
            labels = torch.tensor(labels, dtype=torch.int64)
            area = torch.tensor(area, dtype=torch.float32)
            iscrowd = torch.tensor(iscrowd, dtype=torch.int64)

        return {
            "boxes": boxes,
            "labels": labels,
            "image_id": torch.tensor([image_id], dtype=torch.int64),
            "area": area,
            "iscrowd": iscrowd,
        }

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        if not self._use_real:
            return self._dataset[idx]

        image, raw_target = self._dataset[idx]
        if isinstance(image, Image.Image):
            image = self._image_transform(image)
        targets = self._convert_target(raw_target, idx)
        return {"image": image, "targets": targets}
