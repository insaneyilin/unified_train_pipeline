import importlib
import pkgutil
import warnings
from pathlib import Path


class ModuleRegister:
    def __init__(self):
        self._module_dict = {}

    @property
    def available_names(self):
        return self._module_dict.keys()

    def get(self, key: str):
        return self._module_dict[key]

    def _register_module(self, module_class: type) -> None:
        self._module_dict[module_class.__name__] = module_class

    def register_module(self):
        def _register(cls: type):
            self._register_module(cls)
            return cls

        return _register


MODULE_REGISTER = ModuleRegister()


def build_module(name: str, *args, **kwargs):
    if name not in MODULE_REGISTER.available_names:
        raise ValueError(
            f"{name} is not an available module name. "
            f"Available modules: {list(MODULE_REGISTER.available_names)}")
    return MODULE_REGISTER.get(name)(*args, **kwargs)


def auto_import_modules(package_name: str,
                        package_path: str = None,
                        exclude_patterns=None):
    if exclude_patterns is None:
        exclude_patterns = ["_test", "__pycache__", "utils"]

    if package_path is None:
        package = importlib.import_module(package_name)
        package_path = Path(package.__file__).parent
    else:
        package_path = Path(package_path)

    for module_info in pkgutil.iter_modules([str(package_path)]):
        module_name = module_info.name
        if any(pattern in module_name for pattern in exclude_patterns):
            continue
        if module_name.startswith("_") and module_name != "__init__":
            continue
        try:
            importlib.import_module(f"{package_name}.{module_name}")
        except Exception as e:
            warnings.warn(f"Failed to auto-import {package_name}.{module_name}: {e}",
                          ImportWarning)
