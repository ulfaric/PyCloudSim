from __future__ import annotations
from ipaddress import IPv4Address
from math import inf
from operator import indexOf

import warnings
from typing import TYPE_CHECKING, Any, Callable, List

from Akatosh import Entity
from Akatosh.entity import Entity, EntityList, Resource
from bitmath import GiB

from PyCloudSim import simulation, logger

from .constants import Constants
from .v_cpu import vCPU
from .v_nic import vNIC
from .v_process import vDecoder, vProcess

if TYPE_CHECKING:
    from .v_packet import vPacket


class vHardwareEntity(Entity):
    def __init__(
        self,
        ipc: int | Callable,
        frequency: int | Callable,
        num_cores: int | Callable,
        cpu_tdps: int | float | Callable,
        cpu_mode: int,
        ram: int | Callable,
        rom: int | Callable,
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
        """Create a simulated hardware entity.

        Args:
            ipc (int | Callable): the instructions per cycle (IPC) of the CPU.
            frequency (int | Callable): the frequency of the CPU, in MHz.
            num_cores (int | Callable): the number of cores of the CPU.
            cpu_tdps (int | float | Callable): the thermal design power (TDP) of the CPU, in Watts.
            ram (int | Callable): the RAM of the hardware entity, in GiB.
            rom (int | Callable): the ROM of the hardware entity, in GiB.
            label (str | None, optional): the short name for the entity. Defaults to None.
            create_at (int | float | Callable[..., Any] | None, optional): when the enity should be created. Defaults to None.
            terminate_at (int | float | Callable[..., Any] | None, optional): when the entity should be terminated. Defaults to None.
            precursor (Entity | List[Entity] | None, optional): the presursors that must be terminated before the creation of this entity. Defaults to None.
        """
        super().__init__(label, create_at, terminate_at, precursor)

        self._cpu = vCPU(
            ipc, frequency, num_cores, cpu_tdps, cpu_mode, self, label=f"{label}"
        )
        if callable(ram):
            self._ram = Resource(
                capacity=GiB(round(ram())).bytes, label=f"{self.label}-RAM"
            )
        else:
            self._ram = Resource(capacity=GiB(ram).bytes, label=f"{self.label}-RAM")
        if callable(rom):
            self._rom = Resource(
                capacity=GiB(round(rom())).bytes, label=f"{self.label}-ROM"
            )
        else:
            self._rom = Resource(capacity=GiB(rom).bytes, label=f"{self.label}-ROM")

        if architecture in [Constants.X86, Constants.ARM]:
            self._architecture = architecture
        else:
            raise ValueError(f"Platform {architecture} is not supported.")
        self._NIC = vNIC(host=self, label=f"{self}-NIC")

    def on_creation(self):
        simulation.network.add_node(self)
        self.cpu.create(simulation.now)
        self.NIC.create(simulation.now)
        self.NIC.add_port(
            endpoint=self,
            bandwidth=10000,
            at=simulation.now,
            ip_address=IPv4Address("127.0.0.1"),
        )

    def on_termination(self):
        simulation.network.del_node(self)
        self.cpu.terminate(simulation.now)
        self.NIC.terminate(simulation.now)

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
        
        for event in self.events:
            if event.label == f"{self.label} Power On":
                if at > event.at:
                    return

        @self.instant_event(at, label=f"{self.label} Power On", priority=-1)
        def _power_on() -> None:
            if self.powered_on or self.failed or self.terminated:
                return
            self.cpu.power_on(simulation.now)
            self.NIC.power_on(simulation.now)
            self.on_power_on()
            self.state.append(Constants.POWER_ON)
            if Constants.POWER_OFF in self.state:
                self.state.remove(Constants.POWER_OFF)

    def on_power_on(self) -> None:
        """Called when the hardware entity is powered on"""
        simulation.network.add_node(self)

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
        
        for event in self.events:
            if event.label == f"{self.label} Power Off":
                if at > event.at:
                    return

        @self.instant_event(at, label=f"{self.label} Power Off", priority=-1)
        def _power_off() -> None:
            if self.powered_off or self.failed or self.terminated:
                return
            self.cpu.power_off(simulation.now)
            self.NIC.power_off(simulation.now)
            self.on_power_off()
            self.state.append(Constants.POWER_OFF)
            if Constants.POWER_ON in self.state:
                self.state.remove(Constants.POWER_ON)

    def on_power_off(self) -> None:
        """Called when the hardware entity is powered off"""
        simulation.network.del_node(self)

    def fail(self, at: int | float) -> None:
        """Fail the hardware entity"""

        if self.failed:
            warnings.warn(f"{self.label} is already failed.")
            return

        if self.terminated:
            warnings.warn(f"{self.label} is terminated.")
            return
        
        for event in self.events:
            if event.label == f"{self.label} Fail":
                if at > event.at:
                    return

        @self.instant_event(at, label=f"{self.label} Fail")
        def _fail() -> None:
            if self.failed or self.terminated:
                return
            self.cpu.fail(simulation.now)
            self.NIC.fail(simulation.now)
            self.on_fail()
            self.power_off(simulation.now)
            self.state.append(Constants.FAIL)

    def on_fail(self) -> None:
        """Called when the hardware entity fails"""
        pass

    def receive_packet(self, packet: vPacket) -> None:
        """Receive a packet from the NIC. A decoding virtual process will be created if the packet is successfully received. The decoding process simulates the processing delay."""
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
        decoder = vDecoder(
            packet=packet,
            length=packet.size,
            host=self,
            label=f"{packet} Decoder",
            create_at=simulation.now,
        )
        logger.info(f"{simulation.now}:\t{self} receives {packet}.")

    def drop_packet(self, packet: vPacket) -> None:
        """Drop a packet from the NIC. It should not be called manually."""
        packet.drop()

    def __str__(self) -> str:
        return f"{self.__class__.__name__}-{self.label}"

    @property
    def powered_on(self) -> bool:
        """Return True if the hardware entity is powered on"""
        return Constants.POWER_ON in self.state

    @property
    def powered_off(self) -> bool:
        """Return True if the hardware entity is powered off"""
        return Constants.POWER_OFF in self.state or Constants.POWER_ON not in self.state

    @property
    def failed(self) -> bool:
        """Return True if the hardware component fails"""
        return Constants.FAIL in self.state

    @property
    def cpu(self) -> vCPU:
        """Return the CPU of the hardware entity"""
        return self._cpu

    @property
    def ram(self) -> Resource:
        """Return the RAM of the hardware entity"""
        return self._ram

    @property
    def rom(self) -> Resource:
        """Return the ROM of the hardware entity"""
        return self._rom

    @property
    def NIC(self) -> vNIC:
        """Return the NIC of the hardware entity"""
        return self._NIC

    @property
    def packet_queue(self):
        """Return the packet queue of the hardware entity"""
        return self.NIC.packet_queue

    @property
    def process_queue(self):
        """Return the process queue of the hardware entity"""
        return self.cpu.process_queue

    @property
    def architecture(self):
        """Return the architecture of the hardware entity"""
        return self._architecture

    def cpu_usage(self, duration: int | float | None = None) -> float:
        """Return the CPU usage of the hardware entity"""
        return self.cpu.usage(duration=duration)

    def cpu_utilization(self, duration: int | float | None = None) -> float:
        """Return the CPU utilization of the hardware entity"""
        return self.cpu.utilization(duration=duration)

    def ram_usage(self, duration: int | float | None = None) -> float:
        """Return the RAM usage of the hardware entity"""
        return self.ram.usage(duration=duration)

    def ram_utilization(self, duration: int | float | None = None) -> float:
        """Return the RAM utilization of the hardware entity"""
        return self.ram.utilization(duration=duration)
