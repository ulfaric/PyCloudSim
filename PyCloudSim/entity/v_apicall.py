from __future__ import annotations
from math import inf
from multiprocessing import process
from struct import pack

from typing import Callable, List

from Akatosh import Entity, EntityList

from PyCloudSim import logger, simulation

from .v_microservice import vMicroservice
from .v_packet import vPacket
from .v_process import vContainerProcess
from .v_sofware_entity import vSoftwareEntity
from .v_user import vUser


class vAPICall(vSoftwareEntity):
    """A vAPICall is a software entity that represents an API call."""

    def __init__(
        self,
        src: vMicroservice | vUser,
        dst: vMicroservice | vUser,
        priority: int | Callable[..., int],
        src_process_length: int | Callable[..., int],
        dst_process_length: int | Callable[..., int],
        ack_process_length: int | Callable[..., int],
        num_src_packets: int | Callable[..., int],
        src_packet_size: int | Callable[..., int],
        num_ret_packets: int | Callable[..., int],
        ret_packet_size: int | Callable[..., int],
        num_ack_packets: int | Callable[..., int],
        ack_packet_size: int | Callable[..., int],
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
        """Create a new vAPICall.

        Args:
            src (vMicroservice | vUser): the source of the API call.
            dst (vMicroservice | vUser): the destination of the API call.
            priority (int | Callable[..., int]): the priority of the API call.
            src_process_length (int | Callable[..., int]): the length of the source process.
            dst_process_length (int | Callable[..., int]): the length of the destination process.
            ack_process_length (int | Callable[..., int]): the length of the ack process.
            num_src_packets (int | Callable[..., int]): the number of packets from source.
            src_packet_size (int | Callable[..., int]): the size of the packets from source.
            num_ret_packets (int | Callable[..., int]): the number of packets returned from destination.
            ret_packet_size (int | Callable[..., int]): the size of the packets returned from destination.
            num_ack_packets (int | Callable[..., int]): the number of packets from source for ACK.
            ack_packet_size (int | Callable[..., int]): the size of the packets from source for ACK.
            label (str | None, optional): short description of this vAPICall. Defaults to None.
            create_at (int | float | Callable[..., int] | Callable[..., float] | None, optional): when this vAPICall should be created. Defaults to None.
            terminate_at (int | float | Callable[..., int] | Callable[..., float] | None, optional): when this vAPICall shoudl be terminated. Defaults to None.
            precursor (Entity | List[Entity] | None, optional): the precursor of this vAPICall. Defaults to None.
        """
        super().__init__(label, create_at, terminate_at, precursor)
        self._src = src
        self._dst = dst
        self._type = type
        if callable(priority):
            self._priority = round(priority())
        else:
            self._priority = priority
        if callable(src_process_length):
            self._src_process_length = round(src_process_length())
        else:
            self._src_process_length = src_process_length
        if callable(dst_process_length):
            self._dst_process_length = round(dst_process_length())
        else:
            self._dst_process_length = dst_process_length
        if callable(ack_process_length):
            self._ack_process_length = round(ack_process_length())
        else:
            self._ack_process_length = ack_process_length
        if callable(num_src_packets):
            self._num_src_packets = round(num_src_packets())
        else:
            self._num_src_packets = num_src_packets
        if callable(src_packet_size):
            self._src_packet_size = round(src_packet_size())
        else:
            self._src_packet_size = src_packet_size
        if callable(num_ret_packets):
            self._num_ret_packets = round(num_ret_packets())
        else:
            self._num_ret_packets = num_ret_packets
        if callable(ret_packet_size):
            self._ret_packet_size = round(ret_packet_size())
        else:
            self._ret_packet_size = ret_packet_size
        if callable(num_ack_packets):
            self._num_ack_packets = round(num_ack_packets())
        else:
            self._num_ack_packets = num_ack_packets
        if callable(ack_packet_size):
            self._ack_packet_size = round(ack_packet_size())
        else:
            self._ack_packet_size = ack_packet_size

        self._packets: List[vPacket] = [] # EntityList(label=f"{self} Packets")
        self._processes: List[vContainerProcess] = [] # EntityList(label=f"{self} Processes")
        simulation.api_calls.append(self)

    def on_creation(self):
        super().on_creation()

    def on_initiate(self) -> None:
        """Initiate the vAPICall.
        """
        super().on_initiate()
        if isinstance(self.src, vUser) and isinstance(self.dst, vUser):
            if self.src_process_length > 0:
                logger.warning(
                    f"{simulation.now}:\t{self} source is a vUser, src_instruction_length is ignored."
                )
            if self.dst_process_length > 0:
                logger.warning(
                    f"{simulation.now}:\t{self} destination is a vUser, dst_instruction_length is ignored."
                )
            if self.ack_process_length > 0:
                logger.warning(
                    f"{simulation.now}:\t{self} source is a vUser, ack_instruction_length is ignored."
                )

            if self.num_src_packets <= 0:
                logger.error(
                    f"{simulation.now}:\t{self} invalid vAPICall configuration."
                )
                self.terminate(simulation.now)
                return

            src_packets: List[Entity] = list()
            for i in range(self.num_src_packets):
                src_packet = vPacket(
                    src=self.src,
                    dst=self.dst,
                    size=self.src_packet_size,
                    priority=self.priority,
                    create_at=simulation.now,
                    label=f"{self}-SRC-{i}",
                )
                self.packets.append(src_packet)
                src_packets.append(src_packet)

            ret_packets: List[Entity] = list()
            for i in range(self.num_ret_packets):
                ret_packet = vPacket(
                    src=self.dst,
                    dst=self.src,
                    size=self.ret_packet_size,
                    priority=self.priority,
                    create_at=simulation.now,
                    label=f"{self}-RET-{i}",
                    precursor=src_packets,
                )
                self.packets.append(ret_packet)
                ret_packets.append(ret_packet)

            ack_packets: List[Entity] = list()
            for i in range(self.num_ack_packets):
                ack_packet = vPacket(
                    src=self.src,
                    dst=self.dst,
                    size=self.ack_packet_size,
                    priority=self.priority,
                    create_at=simulation.now,
                    label=f"{self}-ACK-{i}",
                    precursor=ret_packets,
                )
                self.packets.append(ack_packet)
                ack_packets.append(ack_packet)

        elif isinstance(self.src, vUser) and not isinstance(self.dst, vUser):
            if self.src_process_length > 0:
                logger.warning(
                    f"{simulation.now}:\t{self} source is a vUser, src_instruction_length is ignored."
                )
            if self.ack_process_length > 0:
                logger.warning(
                    f"{simulation.now}:\t{self} source is a vUser, ack_instruction_length is ignored."
                )

            if self.num_src_packets <= 0:
                logger.error(
                    f"{simulation.now}:\t{self} invalid vAPICall configuration."
                )
                self.terminate(simulation.now)
                return

            dst_container = self.dst.getContainer()
            
            src_packets: List[Entity] = list()
            for i in range(self.num_src_packets):
                src_packet = vPacket(
                    src=self.src,
                    dst=dst_container,
                    size=self.src_packet_size,
                    priority=self.priority,
                    create_at=simulation.now,
                    label=f"{self}-SRC-{i}",
                )
                self.packets.append(src_packet)
                src_packets.append(src_packet)

            dst_process = vContainerProcess(
                container=self.dst.getContainer(),
                length=self.dst_process_length,
                priority=self.priority,
                precursor=src_packets,
                create_at=simulation.now,
                label=f"{self}-DST",
            )

            ret_packets: List[Entity] = list()
            for i in range(self.num_ret_packets):
                ret_packet = vPacket(
                    src=dst_container,
                    dst=self.src,
                    size=self.ret_packet_size,
                    priority=self.priority,
                    create_at=simulation.now,
                    label=f"{self}-RET-{i}",
                    precursor=dst_process,
                )
                self.packets.append(ret_packet)
                ret_packets.append(ret_packet)

            for i in range(self.num_ack_packets):
                ack_packet = vPacket(
                    src=self.src,
                    dst=dst_container,
                    size=self.ack_packet_size,
                    priority=self.priority,
                    create_at=simulation.now,
                    label=f"{self}-ACK-{i}",
                    precursor=ret_packets,
                )
                self.packets.append(ack_packet)

        elif not isinstance(self.src, vUser) and isinstance(self.dst, vUser):
            if self.dst_process_length > 0:
                logger.warning(
                    f"{simulation.now}:\t{self} destination is a vUser, dst_instruction_length is ignored."
                )
                
            src_container = self.src.getContainer()
            
            src_process = vContainerProcess(
                container=src_container,
                length=self.src_process_length,
                priority=self.priority,
                create_at=simulation.now,
                label=f"{self}-SRC",
            )
            self.processes.append(src_process)

            src_packets: List[Entity] = list()
            for i in range(self.num_ack_packets):
                src_packet = vPacket(
                    src=src_container,
                    dst=self.dst,
                    size=self.src_packet_size,
                    priority=self.priority,
                    create_at=simulation.now,
                    label=f"{self}-SRC-{i}",
                    precursor=src_process,
                )
                self.packets.append(src_packet)
                src_packets.append(src_packet)

            ret_packets: List[Entity] = list()
            for i in range(self.num_ret_packets):
                ret_packet = vPacket(
                    src=self.dst,
                    dst=src_container,
                    size=self.ret_packet_size,
                    priority=self.priority,
                    create_at=simulation.now,
                    label=f"{self}-RET-{i}",
                    precursor=src_packets,
                )
                self.packets.append(ret_packet)
                ret_packets.append(ret_packet)

            ack_process = vContainerProcess(
                container=src_container,
                length=self.ack_process_length,
                priority=self.priority,
                precursor=ret_packets,
                create_at=simulation.now,
                label=f"{self}-ACK",
            )
            self.processes.append(ack_process)

            for i in range(self.num_ack_packets):
                ack_packet = vPacket(
                    src=src_container,
                    dst=self.dst,
                    size=self.ack_packet_size,
                    priority=self.priority,
                    create_at=simulation.now,
                    label=f"{self}-ACK-{i}",
                    precursor=ack_process,
                )
                self.packets.append(ack_packet)

        elif not isinstance(self.src, vUser) and not isinstance(self.dst, vUser):
            
            src_container = self.src.getContainer()
            dst_container = self.dst.getContainer()
            
            src_process = vContainerProcess(
                container=src_container,
                length=self.src_process_length,
                priority=self.priority,
                create_at=simulation.now,
                label=f"{self}-SRC",
            )
            self.processes.append(src_process)

            src_packets: List[Entity] = list()
            for i in range(self.num_src_packets):
                src_packet = vPacket(
                    src=src_container,
                    dst=dst_container,
                    size=self.src_packet_size,
                    priority=self.priority,
                    create_at=simulation.now,
                    label=f"{self}-SRC-{i}",
                    precursor=src_process,
                )
                self.packets.append(src_packet)
                src_packets.append(src_packet)

            dst_process = vContainerProcess(
                container=dst_container,
                length=self.dst_process_length,
                priority=self.priority,
                precursor=src_packets,
                create_at=simulation.now,
                label=f"{self}-DST",
            )
            self.processes.append(dst_process)

            ret_packets: List[Entity] = list()
            for i in range(self.num_ret_packets):
                ret_packet = vPacket(
                    src=dst_container,
                    dst=src_container,
                    size=self.ret_packet_size,
                    priority=self.priority,
                    create_at=simulation.now,
                    label=f"{self}-RET-{i}",
                    precursor=dst_process,
                )
                self.packets.append(ret_packet)
                ret_packets.append(ret_packet)

            ack_process = vContainerProcess(
                container=src_container,
                length=self.ack_process_length,
                priority=self.priority,
                precursor=ret_packets,
                create_at=simulation.now,
                label=f"{self}-ACK",
            )
            self.processes.append(ack_process)

            for i in range(self.num_ack_packets):
                ack_packet = vPacket(
                    src=src_container,
                    dst=dst_container,
                    size=self.ack_packet_size,
                    priority=self.priority,
                    create_at=simulation.now,
                    label=f"{self}-ACK-{i}",
                    precursor=ack_process,
                )
                self.packets.append(ack_packet)

        @self.continuous_event(
            at=simulation.now,
            interval=simulation.min_time_unit,
            duration=inf,
            label=f"{self}-Monitor",
        )
        def monitoring():
            if any([process.failed for process in self.processes]) or any(
                [packet.failed for packet in self.packets]
            ):
                self.fail(simulation.now)
                return

            if all([process.succeed for process in self.processes]) and all(
                [packet.succeed for packet in self.packets]
            ):
                self.success(simulation.now)
                return
            
        logger.info(
            f"{simulation.now}:\t{self} is initiated {self} between {self.src} and {self.dst}."
        )

    def on_termination(self):
        super().on_termination()
        for process in self.processes:
            process.fail(simulation.now)
        logger.info(f"{simulation.now}:\t{self} terminated.")

    def on_destruction(self):
        super().on_termination()
        for process in self.processes:
            process.fail(simulation.now)

    def on_success(self):
        super().on_success()
        logger.info(f"{simulation.now}:\t{self} succeeded.")

    def on_fail(self):
        super().on_fail()
        logger.info(f"{simulation.now}:\t{self} failed.")

    @property
    def src(self) -> vMicroservice | vUser:
        """Return the source of the API call."""
        return self._src

    @property
    def dst(self) -> vMicroservice | vUser:
        """Return the destination of the API call."""
        return self._dst

    @property
    def priority(self) -> int:
        """Return the priority of the API call."""
        return self._priority

    @property
    def packets(self) -> List[vPacket]:
        """Return the packets of the API call."""
        return self._packets

    @property
    def processes(self) -> List[vContainerProcess]:
        """Return the processes of the API call."""
        return self._processes

    @property
    def src_process_length(self) -> int:
        """Return the src_instruction_length"""
        return self._src_process_length

    @property
    def dst_process_length(self) -> int:
        """Return the dst_instruction_length"""
        return self._dst_process_length

    @property
    def ack_process_length(self) -> int:
        """Return the ack_instruction_length"""
        return self._ack_process_length

    @property
    def num_src_packets(self) -> int:
        """Return the num_src_packets"""
        return self._num_src_packets

    @property
    def src_packet_size(self) -> int:
        """Return the src_packet_size"""
        return self._src_packet_size

    @property
    def num_ret_packets(self) -> int:
        """Return the num_ret_packets"""
        return self._num_ret_packets

    @property
    def ret_packet_size(self) -> int:
        """Return the ret_packet_size"""
        return self._ret_packet_size

    @property
    def num_ack_packets(self) -> int:
        """Return the num_ack_packets"""
        return self._num_ack_packets

    @property
    def ack_packet_size(self) -> int:
        """Return the ack_packet_size"""
        return self._ack_packet_size
