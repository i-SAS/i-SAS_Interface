from abc import ABC, abstractmethod
from typing import Callable

from .layout import Layout


class BaseContentLayout(ABC):
    def __init__(
            self,
            cfg: dict,
            ) -> None:
        """Initialize BaseContentLayout

        Args:
            cfg: A config of subpackages.
        """
        Layout.set_cfg(cfg)

    @abstractmethod
    def __call__(self) -> dict[str, Callable]:
        """Create layout of contents.

        Returns:
            A dict of contents, whose keys are named of tabs and values are callable layout instance.
        """
        raise NotImplementedError
