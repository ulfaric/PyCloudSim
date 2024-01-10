import warnings
from abc import ABC, abstractmethod
from typing import Any, Callable, List

from Akatosh import Entity

from PyCloudSim import simulation

from .constants import Constants


class vSoftwareEntityStateError(Exception):
    """Raised when the software entity has a conflicting state."""

    pass


class vSoftwareEntity(Entity, ABC):
    def __init__(
        self,
        label: str | None = None,
        create_at: int
        | float
        | Callable[..., int]
        | Callable[..., float]
        | None = None,
        terminate_at: int
        | float
        | Callable[..., int]
        | Callable[..., float]
        | None = None,
        precursor: Entity | List[Entity] | None = None,
    ) -> None:
        super().__init__(label, create_at, terminate_at, precursor)

    def success(self, at: int | float) -> None:
        """Terminate the process and call on_success()"""

        if self.failed:
            warnings.warn(f"{self} is already terminated unsuccessfully.")
            return

        if self.terminated:
            warnings.warn(f"{self} is already terminated.")
            return

        for event in self.events:
            if event.label == f"{self.label} Success":
                if at > event.at:
                    return

        @self.instant_event(at, label=f"{self.label} Success", priority=-1)
        def _success() -> None:
            if self.succeed or self.terminated:
                return
            # If the process is already terminated successfully, do nothing
            self.on_success()
            self.state.append(Constants.SUCCESS)
            self.terminate(simulation.now)

    def on_success(self) -> None:
        """Called when the software entity is terminated successfully"""
        pass

    def fail(self, at: int | float) -> None:
        """Terminate the software entity and call on_fail()"""

        if self.succeed:
            warnings.warn(f"{self.label} is already terminated successfully.")
            return

        if self.terminated:
            warnings.warn(f"{self.label} is already terminated.")
            return

        if self.failed:
            return

        for event in self.events:
            if event.label == f"{self.label} Fail":
                if at > event.at:
                    return

        @self.instant_event(at, label=f"{self.label} Fail", priority=-1)
        def _fail() -> None:
            if self.failed or self.terminated:
                return
            # If the process is already terminated successfully, do nothing
            self.on_fail()
            self.state.append(Constants.FAIL)
            self.destory(simulation.now)

    def on_fail(self) -> None:
        """Called when the software entity is terminated unsuccessfully"""
        pass

    def initiate(self, at: int | float) -> None:
        """Initiate the software entity and call on_initiate()"""

        if self.initiated:
            warnings.warn(f"{self.label} is already initiated.")
            return

        if self.terminated:
            warnings.warn(f"{self.label} is terminated.")
            return

        @self.instant_event(at, label=f"{self.label} Initiation", priority=-1)
        def _initiate() -> None:
            if self.initiated or self.terminated:
                return
            self.on_initiate()
            self.state.append(Constants.INITIATED)

    def on_initiate(self) -> None:
        """Called when the software entity is initiated"""
        pass

    def on_destruction(self):
        return super().on_destruction()

    def __str__(self) -> str:
        return f"{self.__class__.__name__}-{self.label}"

    @property
    def succeed(self) -> bool:
        """Return true if the software entity is terminated successfully"""
        return Constants.SUCCESS in self.state

    @property
    def failed(self) -> bool:
        """Return true if the software entity is terminated unsuccessfully"""
        return Constants.FAIL in self.state

    @property
    def initiated(self) -> bool:
        """Return true if the software entity is initiated"""
        return Constants.INITIATED in self.state
