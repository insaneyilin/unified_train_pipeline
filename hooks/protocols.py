from typing import Any, Dict, Protocol


class BeforeIterationHook(Protocol):

    def __call__(self, data_dict: Dict[str, Any], context: Dict[str,
                                                                Any]) -> Dict[str,
                                                                              Any]:
        ...


class AfterForwardHook(Protocol):

    def __call__(self, data_dict: Dict[str, Any], context: Dict[str,
                                                                Any]) -> Dict[str,
                                                                              Any]:
        ...


class AfterStepHook(Protocol):

    def __call__(self, data_dict: Dict[str, Any], context: Dict[str,
                                                                Any]) -> Dict[str,
                                                                              Any]:
        ...
