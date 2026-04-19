from typing import Any, Dict

from torchvision import datasets, transforms

from unified_train_pipeline.core.dict_config import DictConfig
from unified_train_pipeline.registry.dataset_register import DATASET_REGISTER


@DATASET_REGISTER.register_dataset()
class MnistDataset:
    """MNIST dataset wrapper returning data_dict-compatible samples."""

    def __init__(self, module_config: DictConfig, global_config: DictConfig):
        transform = transforms.ToTensor()
        self._dataset = datasets.MNIST(
            root=module_config.get("root", "./data"),
            train=bool(module_config.get("train", True)),
            download=bool(module_config.get("download", True)),
            transform=transform,
        )

    def __len__(self):
        return len(self._dataset)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        image, label = self._dataset[idx]
        return {"image": image, "label": label}
