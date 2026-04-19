class EvaluatorRegister:
    def __init__(self):
        self._evaluator_dict = {}

    @property
    def available_names(self):
        return self._evaluator_dict.keys()

    def get(self, key: str):
        return self._evaluator_dict[key]

    def register_evaluator(self):
        def _register(cls):
            self._evaluator_dict[cls.__name__] = cls
            return cls

        return _register


EVALUATOR_REGISTER = EvaluatorRegister()


def build_evaluator(name: str, *args, **kwargs):
    if name not in EVALUATOR_REGISTER.available_names:
        raise ValueError(
            f"{name} is not an available evaluator name. "
            f"Available evaluators: {list(EVALUATOR_REGISTER.available_names)}")
    return EVALUATOR_REGISTER.get(name)(*args, **kwargs)
