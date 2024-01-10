import warnings
from typing import Any, Callable, List

from Akatosh import Entity
from Akatosh.entity import Entity

from PyCloudSim import simulation

from .constants import Constants


class vHardwareComponentStateError(Exception):
    """Raised when the hardware component has a conflicting state."""

    pass


class vHardwareComponent(Entity):
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
        """Base for all hardware components."""
        super().__init__(label, create_at, terminate_at, precursor)

    def on_termination(self):
        self.power_off(simulation.now)

    def power_on(self, at: int | float) -> None:
        """Power on the hardware entity"""

        if self.powered_on:
            warnings.warn(f"{self.label} is already powered on.")
            return

        if self.failed:
            warnings.warn(f"{self.label} is failed.")
            return

        if self.terminated:
            warnings.warn(f"{self.label} is terminated.")
            return

        @self.instant_event(at, label=f"{self.label} Power On", priority=-1)
        def _power_on() -> None:
            if self.powered_on or self.terminated:
                return
            self.on_power_on()
            self.state.append(Constants.POWER_ON)
            if Constants.POWER_OFF in self.state:
                self.state.remove(Constants.POWER_OFF)
            if Constants.FAIL in self.state:
                self.state.remove(Constants.FAIL)

    def on_power_on(self) -> None:
        """Called when the hardware entity is powered on"""
        pass

    def power_off(self, at: int | float) -> None:
        """Power off the hardware entity"""

        if self.powered_off:
            warnings.warn(f"{self.label} is already powered off.")
            return
        if self.failed:
            warnings.warn(f"{self.label} is failed.")
            return

        if self.terminated:
            warnings.warn(f"{self.label} is terminated.")
            return

        @self.instant_event(at, label=f"{self.label} Power Off", priority=-1)
        def _power_off() -> None:
            if self.powered_off or self.terminated:
                return
            self.on_power_off()
            self.state.append(Constants.POWER_OFF)
            if Constants.POWER_ON in self.state:
                self.state.remove(Constants.POWER_ON)

    def on_power_off(self) -> None:
        """Called when the hardware entity is powered off"""
        pass

    def fail(self, at: int | float) -> None:
        """Fail the hardware component"""

        if self.failed:
            warnings.warn(f"{self.label} is already failed.")
            return

        if self.terminated:
            warnings.warn(f"{self.label} is terminated.")
            return

        @self.instant_event(at, label=f"{self.label} Fail")
        def _fail() -> None:
            if self.failed or self.terminated:
                return
            self.on_fail()
            self.power_off(simulation.now)
            self.state.append(Constants.FAIL)

    def on_fail(self) -> None:
        """Called when the hardware component fails"""
        pass

    def __str__(self) -> str:
        return f"{self.__class__.__name__}-{self.label}"

    @property
    def powered_on(self) -> bool:
        """Return True if the hardware component is powered on"""
        return Constants.POWER_ON in self.state

    @property
    def powered_off(self) -> bool:
        """Return True if the hardware component is powered off"""
        return Constants.POWER_OFF in self.state or Constants.POWER_ON not in self.state

    @property
    def failed(self) -> bool:
        """Return True if the hardware component fails"""
        return Constants.FAIL in self.state
