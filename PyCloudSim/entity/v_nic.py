from __future__ import annotations

from ipaddress import IPv4Address
from math import inf
from typing import TYPE_CHECKING, Callable, List

from Akatosh import Entity
from Akatosh.entity import Entity, EntityList, Resource
from bitmath import MiB

from PyCloudSim import logger, simulation

from .constants import Constants
from .v_hardware_component import vHardwareComponent

if TYPE_CHECKING:
    from .v_gateway import vGateway
    from .v_hardware_entity import vHardwareEntity
    from .v_packet import vPacket


class vPort(vHardwareComponent):
    def __init__(
        self,
        nic: vNIC,
        endpoint: vHardwareEntity | vGateway,
        bandwidth: int | Callable[..., int],
        ip_address: IPv4Address | None = None,
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
        """Create a simulated port."""
        super().__init__(label, create_at, terminate_at, precursor)
        self._nic = nic
        self._endpoint = endpoint
        if callable(bandwidth):
            self._bandwidth = Resource(
                capacity=MiB(bandwidth()).bytes, label=f"{self} Bandwidth"
            )
        else:
            self._bandwidth = Resource(
                capacity=MiB(bandwidth).bytes, label=f"{self} Bandwidth"
            )
        self._ip_address = ip_address

    def on_power_on(self) -> None:
        super().on_power_on()

    def on_power_off(self) -> None:
        super().on_power_off()

    def transmit(self, packet: vPacket, transmission_time: int | float):
        """Transmit a packet to the next hop."""
        packet.get(self.bandwidth, packet.size)
        logger.debug(
            f"{simulation.now}:\t{packet} consumes bandwidth {packet.size}/{self.bandwidth.amount}/{self.bandwidth.capacity} from {self}"
        )

        @self.instant_event(
            at=simulation.now + transmission_time,
            label=f"{self} Transmit {packet}",
        )
        def _transmit():
            packet.put(self.bandwidth, packet.size)
            self.nic.packet_queue.remove(packet)
            logger.debug(
                f"{simulation.now}:\t{packet} returns bandwidth {packet.size}/{self.bandwidth.amount}/{self.bandwidth.capacity} from {self}"
            )

    def receive(self, packet: vPacket, transmission_time: int | float):
        """Receive a packet from the previous hop."""
        packet.get(self.bandwidth, packet.size)
        logger.debug(
            f"{simulation.now}:\t{packet} consumes bandwidth {packet.size}/{self.bandwidth.amount}/{self.bandwidth.capacity} from {self}"
        )

        @self.instant_event(
            at=simulation.now + transmission_time,
            label=f"{self} Receive {packet}",
        )
        def _receive():
            packet.put(self.bandwidth, packet.size)
            self.host.receive_packet(packet)
            logger.debug(
                f"{simulation.now}:\t{packet} returns bandwidth {packet.size}/{self.bandwidth.amount}/{self.bandwidth.capacity} from {self}"
            )

    @property
    def nic(self) -> vNIC:
        """Return the NIC of this port."""
        return self._nic

    @property
    def endpoint(self) -> vHardwareEntity | vGateway:
        """Return the endpoint of this NIC."""
        return self._endpoint

    @property
    def host(self):
        """Return the host of this port."""
        return self.nic.host

    @property
    def ip_address(self) -> IPv4Address | None:
        """Return the IP address of this port."""
        return self._ip_address

    @property
    def bandwidth(self) -> Resource:
        """Return the bandwidth of this port."""
        return self._bandwidth

    def usage(self, duration: int | float | None = None):
        """Return the bandwidth usage of this port."""
        return self.bandwidth.usage(duration)

    def utilization(self, duration: int | float | None = None):
        """Return the bandwidth utilization of this port."""
        return self.bandwidth.utilization(duration)


class vNIC(vHardwareComponent):
    def __init__(
        self,
        host: vHardwareEntity | vGateway,
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
        """Create a simulated NIC."""
        super().__init__(label, create_at, terminate_at, precursor)
        self._host = host
        self._ports: List[vPort] = EntityList(label=f"{self} Ports")
        self._packet_queue: List[vPacket] = EntityList(label=f"{self} Packet Queue")

    def on_power_on(self) -> None:
        """Power on the simulated NIC."""
        super().on_power_on()
        for port in self.ports:
            port.power_on(simulation.now)

        @self.continuous_event(
            at=simulation.now,
            interval=simulation.min_time_unit,
            duration=inf,
            label=f"{self} Transmit Packets",
        )
        def _schedule_packets():
            """A continous event to schedule packets in the queue."""
            self.packet_queue.sort(key=lambda packet: packet.priority)
            for packet in self.packet_queue:
                # check if packet is decoded
                if packet.decoded and not packet.in_transmission:
                    logger.debug(f"{simulation.now}:\t{self} is scheduling {packet}.")
                    # find the port to transmit the packet to the next hop
                    try:
                        src_port = [
                            port
                            for port in self.ports
                            if port.endpoint is packet.next_hop
                        ][0]
                    except:
                        raise RuntimeError(
                            f"Can not find a port on {packet.path[0]} to transmit {packet}."
                        )
                    # find the port to receive the packet on the next hop
                    try:
                        dst_port = [
                            port
                            for port in packet.next_hop.NIC.ports
                            if port.endpoint is packet.current_hop
                        ][0]
                    except:
                        raise RuntimeError(
                            f"Can not find a port on {packet.path[1]} to receive {packet}."
                        )
                    logger.debug(
                        f"{simulation.now}:\t{self} found src port {src_port} and dst port {dst_port} for {packet}"
                    )
                    # calculate the available bandwidth and transmission time
                    available_bandwidth = min(
                        src_port.bandwidth.amount, dst_port.bandwidth.amount
                    )
                    logger.debug(
                        f"{simulation.now}:\t{self} found available bandwidth {available_bandwidth} for {packet}"
                    )
                    # check if the packet can be transmitted
                    if available_bandwidth > packet.size:
                        packet.state.append(Constants.INTRANSMISSION)
                        link_speed = min(
                            src_port.bandwidth.capacity, dst_port.bandwidth.capacity
                        )
                        # calculate the transmission time
                        transmission_time = packet.size / link_speed

                        # packet consumes the bandwidth of the src port and returns the bandwidth in future
                        src_port.transmit(packet, transmission_time)

                        # packet consumes the bandwidth of the dst port and returns the bandwidth in future
                        dst_port.receive(packet, transmission_time)

                        logger.info(
                            f"{simulation.now}:\t{packet} in transmission from {src_port.host} to {dst_port.host}"
                        )
                else:
                    # pass packets that have not been decoded
                    pass

    def on_power_off(self) -> None:
        """Power off the simulated NIC."""
        super().on_power_off()
        for event in self.events:
            if event.label == f"{self} Transmit Packets":
                event.cancel()

    def add_port(
        self,
        endpoint: vHardwareEntity | vGateway,
        bandwidth: int | Callable[..., int],
        ip_address: IPv4Address | None,
        at: int | float,
    ):
        """Add a port to this virtual NIC."""

        @self.instant_event(at, label=f"{self} Add Port to {endpoint}")
        def _add_port():
            port = vPort(
                self,
                endpoint,
                bandwidth,
                ip_address=ip_address,
                label=f"{self.label}-{len(self.ports)}",
                create_at=simulation.now,
            )
            self.ports.append(port)

    def remove_port(self, endpoint: vHardwareEntity, at: int | float):
        """Remove a port from this virtual NIC."""

        @self.instant_event(at, label=f"{self} Remove Port to {endpoint}")
        def _remove_port():
            for port in self.ports:
                if port.endpoint is endpoint:
                    port.terminate(simulation.now)

    @property
    def host(self):
        """Return the host of this NIC."""
        return self._host

    @property
    def ports(self):
        """Return the ports of this NIC."""
        return self._ports

    @property
    def packet_queue(self):
        """Return the packet queue of this NIC."""
        return self._packet_queue

    def egress_usage(self, duration: int | float | None = None):
        """Return the egress bandwidth usage of this NIC."""
        return sum([port.usage(duration) for port in self.ports])

    def egress_utilization(self, duration: int | float | None = None):
        """Return the egress bandwidth utilization of this NIC."""
        return sum([port.utilization(duration) for port in self.ports]) / len(
            self.ports
        )

    def ingress_usage(self, duration: int | float | None = None):
        """Return the ingress bandwidth usage of this NIC."""
        connected_nodes = [
            port.endpoint for port in self.ports
        ]
        ingress_usage = 0
        for node in connected_nodes:
            for port in node.NIC.ports:
                if port.endpoint is self.host:
                    ingress_usage += port.usage(duration)
        return ingress_usage
    
    def ingress_utilization(self, duration: int | float | None = None):
        """Return the ingress bandwidth utilization of this NIC."""
        connected_nodes = [
            port.endpoint for port in self.ports
        ]
        ingress_utilization = 0
        for node in connected_nodes:
            for port in node.NIC.ports:
                if port.endpoint is self.host:
                    ingress_utilization += port.utilization(duration)
        return ingress_utilization / len(connected_nodes)