from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from math import inf

from Akatosh import Entity

from PyCloudSim import simulation, logger

if TYPE_CHECKING:
    from ..entity import vVolume, vHost


class VolumeScheduler(ABC, Entity):
    """Base for all container schedulers."""

    def __init__(self) -> None:
        super().__init__(label="Volume Scheduler", create_at=0, precursor=None)
        simulation._volume_scheduler = self

    def on_creation(self):
        super().on_creation()

        @self.continuous_event(
            at=simulation.now,
            interval=simulation.min_time_unit,
            duration=inf,
            label="Scheduling Volumes",
            priority=inf,
        )
        def scheduling():
            for volume in simulation.volumes:
                # skip if container is already scheduled
                if volume.scheduled:
                    continue

                # find a host for the container
                host = self.find_host(volume)
                # if a host is found, allocate the container to the host
                if host:
                    host.allocate_volume(volume)
                else:
                    logger.debug(f"{simulation.now}:\t{volume} cannot be scheduled.")

    def on_termination(self):
        return super().on_termination()

    def on_destruction(self):
        return super().on_destruction()

    @abstractmethod
    def find_host(self, volume: vVolume) -> vHost | None:
        pass


class DefaultVolumeScheduler(VolumeScheduler):
    """Default volume scheduler. It will return the first available host."""

    def __init__(self) -> None:
        super().__init__()

    def find_host(self, volume: vVolume) -> vHost | None:
        for host in simulation.hosts:
            if host.powered_on and host.rom_reservoir.amount >= volume.size:
                return host


class BestfitVolumeScheduler(VolumeScheduler):
    """Bestfit volume scheduler. It will return the host with the least amount of resources."""

    def __init__(self) -> None:
        super().__init__()

    def find_host(self, volume: vVolume) -> vHost | None:
        simulation.hosts.sort(key=lambda host: host.rom_reservoir.amount)
        for host in simulation.hosts:
            if host.powered_on and host.rom_reservoir.amount >= volume.size:
                return host


class WorstfitVolumeScheduler(VolumeScheduler):
    """Worstfit volume scheduler. It will return the host with the most amount of resources."""

    def __init__(self) -> None:
        super().__init__()

    def find_host(self, volume: vVolume) -> vHost | None:
        simulation.hosts.sort(key=lambda host: host.rom_reservoir.amount, reverse=True)
        for host in simulation.hosts:
            if host.powered_on and host.rom_reservoir.amount >= volume.size:
                return host
