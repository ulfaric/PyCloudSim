from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, List

from Akatosh import Entity, Resource
from bitmath import MiB

from PyCloudSim import logger, simulation

from .constants import Constants
from .v_sofware_entity import vSoftwareEntity

if TYPE_CHECKING:
    from .v_host import vHost


class vVolume(vSoftwareEntity):
    def __init__(
        self,
        size: int | Callable[..., Any],
        path: str | None = None,
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

        if callable(size):
            self._store = Resource(MiB(round(size())).bytes)
        else:
            self._store = Resource(MiB(size).bytes)

        self._path = path

        self._host: vHost = None  # type: ignore

        simulation.volumes.append(self)

    def on_creation(self):
        logger.info(f"{simulation.now}:\t{self} is created.")

    def on_termination(self):
        logger.info(f"{simulation.now}:\t{self} is terminated.")

    @property
    def size(self) -> int | float:
        """Returns the size of the volume."""
        return self._store.capacity

    @property
    def path(self) -> str | None:
        """Returns the path of the volume."""
        return self._path

    @property
    def scheduled(self):
        """Return whether the volume has been scheduled."""
        return Constants.SCHEDULED in self.state
