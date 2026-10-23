"""Retired local simulator; experiments must use ns-3 with 5G-LENA."""


class DiscreteEventRANSimulator:
    def __init__(self, *args, **kwargs) -> None:
        raise RuntimeError(
            "DiscreteEventRANSimulator is disabled. "
            "Run experiments with ns-3 and 5G-LENA."
        )
