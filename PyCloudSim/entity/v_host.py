from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, List

from Akatosh import Entity, EntityList, Resource
from bitmath import GiB

from PyCloudSim import logger, simulation

from .constants import Constants
from .v_hardware_entity import vHardwareEntity

if TYPE_CHECKING:
    from .v_container import vContainer
    from .v_volume import vVolume


class vHostMEMOverload(Exception):
    """Raised when the host's memory is overloaded."""

    pass


class vHost(vHardwareEntity):
    def __init__(
        self,
        ipc: int | Callable[..., Any],
        frequency: int | Callable[..., Any],
        num_cores: int | Callable[..., Any],
        cpu_tdps: int | float | Callable[..., Any],
        cpu_mode: int,
        ram: int | Callable[..., Any],
        rom: int | Callable[..., Any],
        architecture: str = Constants.X86,
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
        """Create a simulated host.

        Args:
            ipc (int | Callable[..., Any]): the instructions per cycle (IPC) of the CPU.
            frequency (int | Callable[..., Any]): the frequency of the CPU.
            num_cores (int | Callable[..., Any]): the number of cores of the CPU.
            cpu_tdps (int | float | Callable[..., Any]): the thermal design power (TDP) of the CPU.
            ram (int | Callable[..., Any]): the RAM capacity of the host, in GiB.
            rom (int | Callable[..., Any]): the ROm capacity of the host, in GiB.
            label (str | None, optional): the short name of the host. Defaults to None.
            create_at (int | float | Callable[..., Any] | None, optional): when this host should be created. Defaults to None.
            terminate_at (int | float | Callable[..., Any] | None, optional): when this host should be terminated. Defaults to None.
            precursor (Entity | List[Entity] | None, optional): the precursors that must be terminated before this host is created. Defaults to None.
        """
        super().__init__(
            ipc,
            frequency,
            num_cores,
            cpu_tdps,
            cpu_mode,
            ram,
            rom,
            architecture,
            label,
            create_at,
            terminate_at,
            precursor,
        )

        if callable(ram):
            self._ram_reservoir = Resource(
                capacity=GiB(round(ram())).bytes, label=f"{self} RAM Reservoir"
            )
        else:
            self._ram_reservoir = Resource(
                capacity=GiB(ram).bytes, label=f"{self} RAM Reservoir"
            )

        if callable(rom):
            self._rom_reservoir = Resource(
                capacity=GiB(round(rom())).bytes, label=f"{self} ROM Reservoir"
            )
        else:
            self._rom_reservoir = Resource(
                capacity=GiB(rom).bytes, label=f"{self} ROM Reservoir"
            )

        self._container_queue: List[vContainer] = EntityList(
            label=f"{self} Container Queue"
        )
        self._volume_queue: List[vVolume] = EntityList(label=f"{self} Volume Queue")

    def on_power_off(self) -> None:
        for container in self.container_queue:
            container.terminate(at=simulation.now)

    def allocate_container(self, container: vContainer) -> None:
        """Allocate a container to the host. This will start the creation of the container."""
        self._container_queue.append(container)
        container.get(self.cpu_reservoir, container.cpu)
        container.get(self.ram_reservoir, container.ram)
        container.get(self.rom_reservoir, container.image_size)
        container._host = self
        container.state.append(Constants.SCHEDULED)
        container.initiate(simulation.now)
        logger.info(
            f"{simulation.now}:\t{container} is allocated to {self}, available CPU {self.cpu_reservoir.utilization():.2f}% | RAM {self.ram_reservoir.utilization():.2f}% | ROM {self.rom_reservoir.utilization():.2f}%."
        )

    def allocate_volume(self, volume: vVolume) -> None:
        self._volume_queue.append(volume)
        volume.get(self.rom_reservoir, volume.size)
        volume._host = self
        volume.state.append(Constants.SCHEDULED)
        logger.info(
            f"{simulation.now}:\t{volume} is allocated to {self}, available ROM {self.rom_reservoir.utilization():.2f}%."
        )

    @property
    def cpu_reservoir(self):
        """Return the CPU reservoir, used in container allocation."""
        return self.cpu.computational_power_reservoir

    @property
    def ram_reservoir(self):
        """Return the RAM reservoir, used in container allocation."""
        return self._ram_reservoir

    @property
    def rom_reservoir(self):
        """Return the ROM reservoir, used in container allocation."""
        return self._rom_reservoir

    @property
    def container_queue(self):
        """Return the container queue, all the containers allocated on the host."""
        return self._container_queue

    @property
    def volume_queue(self):
        """Return the volume queue, all the volumes allocated on the host."""
        return self._volume_queue

    @property
    def ip_address(self):
        """Return the IP address of the host."""
        return [port.ip_address for port in self.NIC.ports]
