from __future__ import annotations
from math import inf
from operator import indexOf
from typing import TYPE_CHECKING, List

from Akatosh import Entity, EntityList, Resource
from Akatosh.entity import Entity

from PyCloudSim import simulation, logger

from .v_nic import vNIC
from .constants import Constants

if TYPE_CHECKING:
    from .v_packet import vPacket
    from .v_user import vUser


class vGateway(Entity):
    def __init__(
        self,
        label: str | None = None,
    ) -> None:
        """Create a virtual gateway.

        Args:
            label (str | None, optional): short description of the gateway. Defaults to None.
        """
        super().__init__(label=label, create_at=0)

        self._users: List[vUser] = EntityList()
        self._NIC = vNIC(host=self, label=f"{self}-NIC")
        self._ram = Resource(capacity=inf, label=f"{self}-RAM")
        self._cpu = None

    def on_creation(self):
        simulation.topology.add_node(self)
        self.NIC.create(simulation.now)
        self.NIC.power_on(simulation.now)

    def on_termination(self):
        return super().on_termination()

    def on_destruction(self):
        return super().on_destruction()

    def receive_packet(self, packet: vPacket) -> None:
        """Receive a packet from the NIC."""
        if packet.decoded:
            packet.state.remove(Constants.DECODED)
        if packet.in_transmission:
            packet.state.remove(Constants.INTRANSMISSION)
        try:
            packet.get(self.ram, packet.size)
        except:
            packet.drop()
            return
        self.packet_queue.append(packet)
        packet._current_hop = self
        if packet.current_hop is not packet.dst_host:
            packet._next_hop = packet.path[indexOf(packet.path, self) + 1]
        else:
            packet.success(simulation.now)
        logger.info(f"{simulation.now}:\t{self} receives {packet}.")

    @property
    def users(self) -> List[vUser]:
        """Returns the users asscociated with the gateway."""
        return self._users

    @property
    def NIC(self) -> vNIC:
        """Return the NIC of this virtual gateway."""
        return self._NIC

    @property
    def ram(self) -> Resource:
        """Return the RAM of the virtual gateway which has infinite capacity."""""
        return self._ram

    @property
    def cpu(self):
        """Return the CPU of the virtual gateway which is none, created for avoid typing issues."""
        return self._cpu

    @property
    def packet_queue(self):
        """Return the packet queue of the hardware entity"""
        return self.NIC.packet_queue
