from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from math import inf

from Akatosh import Entity

from PyCloudSim import simulation, logger

if TYPE_CHECKING:
    from ..entity import vContainer, vHost


class ContainerScheduler(ABC, Entity):
    """Base for all container schedulers."""

    def __init__(self) -> None:
        super().__init__(label="Container Scheduler", create_at=0)
        simulation._container_scheduler = self

    def on_creation(self):
        super().on_creation()

        @self.continuous_event(
            at=simulation.now,
            interval=simulation.min_time_unit,
            duration=inf,
            label="Scheduling Containers",
            priority=inf,
        )
        def _scheduling():
            simulation.containers.sort(key=lambda container: container.priority)
            for container in simulation.containers:
                # skip if container is already scheduled
                if container.scheduled:
                    continue
                
                # skip if not all volumes are scheduled
                if not all([volume.scheduled for volume in container.volumes]):
                    continue

                # find a host for the container
                host = self.find_host(container)
                # if a host is found, allocate the container to the host
                if host:
                    host.allocate_container(container)
                else:
                    logger.debug(
                        f"{simulation.now}:\tContainer {container.label} cannot be scheduled."
                    )

    def on_termination(self):
        return super().on_termination()

    def on_destruction(self):
        return super().on_destruction()

    @abstractmethod
    def find_host(self, container: vContainer) -> vHost | None:
        pass


class DefaultContainerScheduler(ContainerScheduler):
    """Default container scheduler. It will return the first available host."""

    def __init__(self) -> None:
        super().__init__()

    def find_host(self, container: vContainer) -> vHost | None:
        for host in simulation.hosts:
            if (
                host.powered_on
                and host.ram_reservoir.amount >= container.ram
                and host.cpu_reservoir.amount >= container.cpu
                and host.rom_reservoir.amount >= container.image_size
            ):
                return host


class BestfitContainerScheduler(ContainerScheduler):
    """Bestfit container scheduler. It will return the host with the least amount of resources."""

    def __init__(self) -> None:
        super().__init__()

    def find_host(self, container: vContainer) -> vHost | None:
        simulation.hosts.sort(key=lambda host: host.rom_reservoir.amount)
        simulation.hosts.sort(key=lambda host: host.ram_reservoir.amount)
        simulation.hosts.sort(key=lambda host: host.cpu_reservoir.amount)
        for host in simulation.hosts:
            if (
                host.powered_on
                and host.ram_reservoir.amount >= container.ram
                and host.cpu_reservoir.amount >= container.cpu
                and host.rom_reservoir.amount >= container.image_size
            ):
                return host


class WorstfitContainerScheduler(ContainerScheduler):
    """Worstfit container scheduler. It will return the host with the most amount of resources."""

    def __init__(self) -> None:
        super().__init__()

    def find_host(self, container: vContainer) -> vHost | None:
        simulation.hosts.sort(key=lambda host: host.rom_reservoir.amount, reverse=True)
        simulation.hosts.sort(key=lambda host: host.ram_reservoir.amount, reverse=True)
        simulation.hosts.sort(key=lambda host: host.cpu_reservoir.amount, reverse=True)
        for host in simulation.hosts:
            if (
                host.powered_on
                and host.ram_reservoir.amount >= container.ram
                and host.cpu_reservoir.amount >= container.cpu
                and host.rom_reservoir.amount >= container.image_size
            ):
                return host
