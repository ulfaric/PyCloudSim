from __future__ import annotations

from math import inf
from typing import TYPE_CHECKING, Callable, List, Tuple

from Akatosh import Entity, EntityList
from bitmath import MiB

from PyCloudSim import logger, simulation
from PyCloudSim.entity.v_volume import vVolume

from .constants import Constants
from .v_process import vDeamon, vProcess
from .v_sofware_entity import vSoftwareEntity

if TYPE_CHECKING:
    from .v_host import vHost


class vContainerMEMOverload(Exception):
    """Raised when the container's memory is overloaded."""

    pass


class vContainer(vSoftwareEntity):
    def __init__(
        self,
        cpu: int | Callable[..., int],
        ram: int | Callable[..., int],
        image_size: int | Callable[..., int],
        cpu_limit: int | Callable[..., int] | None = None,
        ram_limit: int | Callable[..., int] | None = None,
        volumes: List[Tuple[int, str, str]] = [],
        priority: int | Callable[..., int] = 0,
        deamon: bool | Callable[..., bool] = False,
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
        """Create a simulated container.

        Args:
            cpu (int | Callable[..., int]): the requested CPU of the container.
            ram (int | Callable[..., int]): the requested RAM of the container.
            image_size (int | Callable[..., int]): the image size of the container.
            cpu_limit (int | Callable[..., int] | None, optional): the limited CPU of the container. Defaults to None, means there is no limitation.
            ram_limit (int | Callable[..., int] | None, optional): the limited RAM of the container. Defaults to None, means there is no limitation.
            priority (int | Callable[..., int], optional): the priority of the container. Defaults to 0.
            deamon (bool | Callable[..., bool], optional): true if the container has a constantly running process. Defaults to False.
            label (str | None, optional): the short description of the container. Defaults to None.
            create_at (int | float | Callable[..., int] | Callable[..., float] | None, optional): when this container should be created. Defaults to None.
            terminate_at (int | float | Callable[..., int] | Callable[..., float] | None, optional): when this container should be terminated. Defaults to None means it will not be terminated unless it is failed or termination is forced.
            precursor (Entity | List[Entity] | None, optional): the entity that this container must not be created before. Defaults to None.
        """
        super().__init__(label, create_at, terminate_at, precursor)

        if callable(cpu):
            self._cpu = round(cpu())
        else:
            self._cpu = cpu

        if callable(ram):
            self._ram = MiB(round(ram())).bytes
        else:
            self._ram = MiB(ram).bytes

        if callable(image_size):
            self._image_size = MiB(round(image_size())).bytes
        else:
            self._image_size = MiB(image_size).bytes

        if callable(ram_limit):
            self._ram_limit = MiB(round(ram_limit())).bytes
        elif ram_limit is not None:
            self._ram_limit = MiB(ram_limit).bytes
        else:
            self._ram_limit = inf

        if callable(cpu_limit):
            self._cpu_limit = round(cpu_limit())
        elif cpu_limit is not None:
            self._cpu_limit = cpu_limit
        else:
            self._cpu_limit = inf

        self._volumes_descriptions = volumes
        self._volumes = EntityList(label=f"{self} Volumes")

        if callable(priority):
            self._priority = round(priority())
        else:
            self._priority = priority

        if callable(deamon):
            self._deamon = deamon()
        else:
            self._deamon = deamon

        self._host: vHost | None = None
        self._deamon_process: vProcess | None = None
        self._process_queue: List[vProcess] = EntityList(label=f"{self} Process Queue")
        self._cpu_usage = 0.0
        self._ram_usage = 0

        simulation.containers.append(self)

    def on_creation(self):
        for volume_description in self._volumes_descriptions:
            volume = vVolume(
                size=volume_description[0],
                path=volume_description[1],
                label=volume_description[2],
                create_at=simulation.now,
            )
            self.volumes.append(volume)

        logger.info(f"{simulation.now}:\t{self} is created.")

    def on_termination(self):
        for process in self.process_queue:
            process.fail(simulation.now)
        for volume in self.volumes:
            volume.terminate(simulation.now)
        logger.info(f"{simulation.now}:\t{self} is terminated.")

    def on_destruction(self):
        for process in self.process_queue:
            process.fail(simulation.now)
        for volume in self.volumes:
            volume.destroy(simulation.now)
        logger.info(f"{simulation.now}:\t{self} is failed.")

    def on_success(self) -> None:
        super().on_success()

    def on_fail(self) -> None:
        super().on_fail()
        logger.info(f"{simulation.now}:\t{self} is failed.")

    def on_initiate(self):
        """Initiate the container."""
        super().on_initiate()
        if self.host is None:
            raise RuntimeError(f"{self} can not be initiated without a host.")
        if self.deamon:
            deamon_length = round(
                (self.cpu / 1000) * self.host.cpu.ipc * self.host.cpu.frequency
            )
            self._deamon_process = vDeamon(
                length=deamon_length,
                container=self,
                priority=-1,
                label=f"{self.label}",
                create_at=simulation.now,
            )
        logger.info(f"{simulation.now}:\t{self} is initiated.")

    @property
    def cpu(self):
        """Return the requested CPU of the container."""
        return self._cpu

    @property
    def cpu_limit(self) -> float | int:
        """Return the CPU limit of the container."""
        return self._cpu_limit

    @property
    def ram(self):
        """Return the requested RAM of the container."""
        return self._ram

    @property
    def ram_limit(self) -> float | int:
        """Return the RAM limit of the container."""
        return self._ram_limit

    @property
    def image_size(self):
        """Return the image size of the container."""
        return self._image_size

    @property
    def priority(self):
        """Return the priority of the container."""
        return self._priority

    @property
    def scheduled(self):
        """Return whether the container has been scheduled."""
        return Constants.SCHEDULED in self.state

    @property
    def initiated(self):
        """Return whether the container has been initiated."""
        return Constants.INITIATED in self.state

    @property
    def deamon(self):
        """Return whether the container is a deamon."""
        return self._deamon

    @property
    def deamon_process(self):
        """Return the deamon process of the container."""
        return self._deamon_process

    @property
    def host(self):
        """Return the host of the container."""
        if self._host is None:
            raise RuntimeError(f"{self} has not been allocated on a host.")
        return self._host

    @property
    def cpu_usage(self):
        """Return the CPU usage of the container."""
        return self._cpu_usage

    @property
    def cpu_utilization(self):
        """Return the CPU utilization of the container."""
        return self._cpu_usage / self.cpu_limit

    @property
    def ram_usage(self):
        """Return the RAM usage of the container."""
        return self._ram_usage

    @property
    def ram_utilization(self):
        """Return the RAM utilization of the container."""
        return self._ram_usage / self.ram_limit

    @property
    def process_queue(self):
        """Return the process queue of the container."""
        return self._process_queue

    @property
    def volumes(self):
        """Return the volumes of the container."""
        return self._volumes