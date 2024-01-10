from __future__ import annotations

from abc import ABC, abstractmethod
from math import inf
from typing import Callable

from Akatosh import Entity

from PyCloudSim import logger, simulation


class Monitor(Entity, ABC):
    def __init__(
        self,
        label: str,
        sample_period: int | float | Callable[..., int] | Callable[..., float] = 0.1,
    ) -> None:
        """Base class for all monitors

        Args:
            label (str): the short name of the monitor.
            sample_period (int | float | Callable[..., int] | Callable[..., float], optional): the sample period. Defaults to 0.1.
        """
        super().__init__(label=label, create_at=0)

        if callable(sample_period):
            self._sample_period = sample_period()
        else:
            self._sample_period = sample_period

    def on_creation(self):
        @self.continuous_event(
            at=simulation.now,
            interval=self._sample_period,
            duration=inf,
            label=f"{self.label} Observer",
        )
        def _observe():
            self.on_observation()
            
    def on_termination(self):
        return super().on_termination()
    
    def on_destruction(self):
        return super().on_destruction()

    @abstractmethod
    def on_observation(self, *arg, **kwargs):
        """The method to be called at each observation/sample."""
        pass

    @property
    def sample_period(self):
        """Return the sample period of the monitor."""
        return self._sample_period