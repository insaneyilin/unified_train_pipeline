class DatasetRegister:
    def __init__(self):
        self._dataset_dict = {}

    @property
    def available_names(self):
        return self._dataset_dict.keys()

    def get(self, key: str):
        return self._dataset_dict[key]

    def register_dataset(self):
        def _register(cls):
            self._dataset_dict[cls.__name__] = cls
            return cls

        return _register


DATASET_REGISTER = DatasetRegister()


def build_dataset(name: str, *args, **kwargs):
    if name not in DATASET_REGISTER.available_names:
        raise ValueError(
            f"{name} is not an available dataset name. "
            f"Available datasets: {list(DATASET_REGISTER.available_names)}")
    return DATASET_REGISTER.get(name)(*args, **kwargs)
