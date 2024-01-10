from __future__ import annotations

from random import randbytes
from typing import TYPE_CHECKING, Callable, List

from Akatosh import Entity

from PyCloudSim import logger, simulation

from .constants import Constants
from .v_sofware_entity import vSoftwareEntity

if TYPE_CHECKING:
    from .v_container import vContainer
    from .v_gateway import vGateway
    from .v_hardware_entity import vHardwareEntity
    from .v_user import vUser


class vPacket(vSoftwareEntity):
    def __init__(
        self,
        src: vContainer | vUser,
        dst: vContainer | vUser,
        size: int | Callable[..., int],
        priority: int | Callable[..., int],
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
        """Create a simulated packet."""
        super().__init__(label, create_at, terminate_at, precursor)
        self._src = src
        self._src_host = src.host
        self._dst = dst
        self._dst_host = dst.host
        if callable(size):
            self._size = size()
        else:
            self._size = size
        if callable(priority):
            self._priority = priority()
        else:
            self._priority = priority
        self._content = bytes()
        self._path: List[vHardwareEntity | vGateway] = []
        self._current_hop: vHardwareEntity | vGateway = None  # type: ignore
        self._next_hop: vHardwareEntity | vGateway = None  # type: ignore

    def on_creation(self):
        """Creation procedure of the simulated packet."""
        super().on_creation()
        logger.info(f"{simulation.now}:\t{self} is created.")
        self.initiate(simulation.now)

    def on_initiate(self) -> None:
        """The initiation procedure of the simulated packet."""
        super().on_initiate()
        # generate the random bytes content
        self._content = randbytes(self.size)
        # find the shortest path from src to dst
        self._path = simulation.network.route(self.src_host, self.dst_host)  # type: ignore
        if len(self.path) == 1:
            self._path = [self.path[0], self.path[0]]
        self._current_hop = self.path[0]
        self._next_hop = self.path[1]
        # inject the packet to its src
        try:
            self.get(self.src_host.ram, self.size)
        except:
            # drop the packet if its src does not have enough ram
            self.drop()
            return
        self.state.append(Constants.DECODED)
        self.src_host.packet_queue.append(self)
        logger.info(f"{simulation.now}:\t{self} is initiated.")

    def on_termination(self):
        """Termination procedure of the simulated packet."""
        super().on_termination()
        logger.info(f"{simulation.now}:\tPacket {self.label} is terminated.")

    def on_fail(self):
        """Failure procedure of the simulated packet."""
        super().on_fail()
        logger.info(f"{simulation.now}:\tPacket {self.label} is dropped.")

    def drop(self):
        """Drop the simulated packet which calls the fail procedure."""
        self.fail(simulation.now)

    @property
    def src(self):
        """return the source of the packet, could be a simulated user or container."""
        return self._src

    @property
    def src_host(self):
        """return the source host of the packet, could be a simulated host or gateway."""
        return self._src_host

    @property
    def dst(self):
        """return the destination of the packet, could be a simulated user or container."""
        return self._dst

    @property
    def dst_host(self):
        """return the destination host of the packet, could be a simulated host or gateway."""
        return self._dst_host

    @property
    def path(self):
        """return the path of the packet."""
        return self._path

    @property
    def size(self) -> int:
        """return the size of the packet."""
        return self._size

    @property
    def content(self) -> bytes:
        """return the content of the packet."""
        return self._content

    @property
    def priority(self) -> int:
        """return the priority of the packet."""
        return self._priority

    @property
    def current_hop(self):
        """return the current hop of the packet."""
        return self._current_hop

    @property
    def next_hop(self):
        """return the next hop of the packet."""
        return self._next_hop

    @property
    def decoded(self) -> bool:
        """return True if the packet is decoded. This happens after the asscoiated decoder process is executed."""
        return Constants.DECODED in self.state

    @property
    def in_transmission(self) -> bool:
        """return True if the packet is in transmission."""
        return Constants.INTRANSMISSION in self.state
