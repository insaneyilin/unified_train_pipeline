class VisualizerRegister:
    def __init__(self):
        self._visualizer_dict = {}

    @property
    def available_names(self):
        return self._visualizer_dict.keys()

    def get(self, key: str):
        return self._visualizer_dict[key]

    def register_visualizer(self):
        def _register(cls):
            self._visualizer_dict[cls.__name__] = cls
            return cls

        return _register


VISUALIZER_REGISTER = VisualizerRegister()


def build_visualizer(name: str, *args, **kwargs):
    if name not in VISUALIZER_REGISTER.available_names:
        raise ValueError(
            f"{name} is not an available visualizer name. "
            f"Available visualizers: {list(VISUALIZER_REGISTER.available_names)}")
    return VISUALIZER_REGISTER.get(name)(*args, **kwargs)
