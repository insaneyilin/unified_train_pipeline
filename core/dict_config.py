import sys
from pathlib import Path

import yaml

_VERSION_CHECKED = False


def _check_version_requirements():
    global _VERSION_CHECKED
    if _VERSION_CHECKED:
        return

    python_version = sys.version_info
    if python_version < (3, 7):
        raise RuntimeError(
            "Python 3.7+ is required for dict order preservation. "
            f"Current version: {python_version.major}.{python_version.minor}.{python_version.micro}"
        )

    _VERSION_CHECKED = True


_check_version_requirements()


class DictConfig(dict):
    """Lightweight dict-like config with attribute access and freeze support."""

    def __init__(self, data=None, **kwargs):
        super().__init__()
        self._freeze = False
        self.add(data, **kwargs)

    def get_freeze_state(self):
        return self._freeze

    def __setattr__(self, key, value):
        if key == "_freeze":
            super().__setattr__(key, value)
            return

        if "_freeze" in self.__dict__ and self._freeze:
            raise RuntimeError(
                "Config is frozen and cannot be modified. Call unfreeze() first if needed."
            )

        if isinstance(value, (list, tuple)):
            value = [
                self.__class__(x) if isinstance(x, dict) or
                (isinstance(x, str) and x.endswith(".yaml")) else x
                for x in value
            ]
        elif isinstance(value, dict):
            value = self.__class__(value)
        elif isinstance(value, str) and value.endswith(".yaml"):
            value = self.__class__(value)

        super().__setattr__(key, value)
        super().__setitem__(key, value)

    __setitem__ = __setattr__

    def add(self, data=None, **kwargs):
        if isinstance(data, (str, Path)) and str(data).endswith(".yaml"):
            with open(data, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        elif data is None:
            data = {}

        data.update(kwargs)
        for key, value in data.items():
            if key in self and isinstance(self[key], self.__class__):
                if isinstance(value, dict):
                    self[key].add(value)
                    value = self[key]
                elif isinstance(value, str) and value.endswith(".yaml"):
                    self[key].add(value)
                    value = self[key]
                else:
                    raise TypeError(f"{key}'s value should be a dict or yaml")
            setattr(self, key, value)

        if isinstance(data, self.__class__):
            self._freeze = data.get_freeze_state()

    def pop(self, key, default=None):
        delattr(self, key)
        return super().pop(key, default)

    def to_dict(self):
        new_dict = {}
        for key, value in self.items():
            if isinstance(value, self.__class__):
                new_dict[key] = value.to_dict()
            elif isinstance(value, list):
                new_dict[key] = [
                    x.to_dict() if isinstance(x, self.__class__) else x
                    for x in value
                ]
            else:
                new_dict[key] = value
        return new_dict

    def copy(self):
        return self.__class__(self)

    def freeze(self):
        self._freeze = True
        for value in self.values():
            if isinstance(value, self.__class__):
                value.freeze()
            elif isinstance(value, list):
                for x in value:
                    if isinstance(x, self.__class__):
                        x.freeze()

    def unfreeze(self):
        self._freeze = False
        for value in self.values():
            if isinstance(value, self.__class__):
                value.unfreeze()
            elif isinstance(value, list):
                for x in value:
                    if isinstance(x, self.__class__):
                        x.unfreeze()
