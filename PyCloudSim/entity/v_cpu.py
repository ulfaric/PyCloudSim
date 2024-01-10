from __future__ import annotations

from math import inf
from typing import TYPE_CHECKING, Callable, List

from Akatosh import Entity, EntityList, Resource
from Akatosh.entity import Entity

from PyCloudSim import logger, simulation

from .v_cpu_core import vCPUCore
from .v_hardware_component import vHardwareComponent

if TYPE_CHECKING:
    from .v_hardware_entity import vHardwareEntity
    from .v_process import vProcess, vContainerProcess, vDeamon, vDecoder


class vCPU(vHardwareComponent):
    def __init__(
        self,
        ipc: int | Callable,
        frequency: int | Callable,
        num_cores: int | Callable,
        tdp: int | float | Callable,
        mode: int,
        host: vHardwareEntity | None = None,
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
        """Create a simulated CPU.

        Args:
            ipc (int | Callable): the instructions per cycle (IPC) of the CPU core.
            frequency (int | Callable): the frequency of the CPU core.
            num_cores (int | Callable): the number of cores of the CPU.
            tdp (int | float | Callable): the thermal design power (TDP) of the CPU.
            mode (int): 1 or 2, the mode of the CPU.
            host (vHardwareEntity | None, optional): the host of this CPU. Defaults to None.
            label (str | None, optional): the short description of the CPU. Defaults to None.
            create_at (int | float | Callable[..., int] | Callable[..., float] | None, optional): when this CPU should be created. Defaults to None.
            terminate_at (int | float | Callable[..., int] | Callable[..., float] | None, optional): when this CPU should be terminated. Defaults to None.
            precursor (Entity | List[Entity] | None, optional): the entity that this CPU must not be created before. Defaults to None.
        """
        super().__init__(label, create_at, terminate_at, precursor)

        # assign attributes
        if callable(ipc):
            self._ipc = round(ipc())
        else:
            self._ipc = ipc

        if callable(frequency):
            self._frequency = round(frequency())
        else:
            self._frequency = frequency

        if callable(num_cores):
            self._num_cores = round(num_cores())
        else:
            self._num_cores = num_cores

        if callable(tdp):
            self._tdp = tdp()
        else:
            self._tdp = tdp

        self._mode = mode

        self._process_queue: List[vProcess | vContainerProcess | vDeamon | vDecoder] = EntityList(label=f"{self}-Process Queue")
        self._cores: List[vCPUCore] = EntityList(label=f"vCPU {self}_Cores")
        self._computational_power_reservoir = Resource(
            capacity=1000 * self.num_cores,
            label=f"{self}-Computational Power Reservoir",
        )
        self._host = host

    def on_creation(self):
        # create cores
        for i in range(self._num_cores):
            self.cores.append(
                vCPUCore(
                    self._ipc,
                    self._frequency,
                    label=f"{self.label}-{i}",
                    create_at=simulation.now,
                )
            )

    def on_termination(self):
        # terminate cores
        for core in self._cores[:]:
            core.terminate(simulation.now)

    def on_power_on(self) -> None:
        """Power on the CPU, also starts the process scheduling."""
        # power on all the cores
        for core in self.cores:
            core.power_on(at=simulation.now)

        # start process scheduling
        @self.continuous_event(
            at=simulation.now,
            interval=self.instruction_cycle,
            duration=inf,
            label=f"{self} Scheduling process",
        )
        def _schedule_process():
            # sort the process queue by priority
            self.process_queue.sort(key=lambda process: process.priority, reverse=False)
            for process in self.process_queue:
                # calculate the number of schedulable instructions
                if process.container is None:
                    container_cpu_capacity = inf
                else:
                    container_cpu_capacity = round(
                        ((process.container.cpu_limit - process.container.cpu_usage) / 1000)
                        * (self.ipc * self.frequency)
                    )
                schedulable_instructions = min(
                    [len(process.unscheduled_instructions), container_cpu_capacity]
                )
                if schedulable_instructions <= 0:
                    continue
                logger.debug(
                    f"{simulation.now}:\t{self} is executing {schedulable_instructions} instructions of {process}."
                )
                try:
                    while schedulable_instructions > 0:
                        # get and sort available cores
                        available_cores = [
                            core
                            for core in self.cores
                            if core.computational_power.amount > 0
                        ]
                        if len(available_cores) == 0:
                            break
                        available_cores.sort(
                            key=lambda core: core.computational_power.amount,
                            reverse=True,
                        )
                        # mode 1: assign one instruction to one core, then move on to the next core
                        if self.mode == 1:
                            core = available_cores[0]
                            # get the next instruction
                            instruction = process.unscheduled_instructions.pop(0)
                            # update the host ram usage
                            if process.host is None:
                                raise RuntimeError()
                            # a value error exception will be raised if fail to distribute the ram space
                            instruction.get(process.host.ram, instruction.length)
                            # update the container's ram usage
                            if process.container is not None:
                                process.container._ram_usage += instruction.length
                                # break the loop if container's ram usage exceeds the limit
                                if (
                                    process.container.ram_usage
                                    > process.container.ram_limit
                                ):
                                    raise Exception()
                                # update the container's cpu usage
                                process.container._cpu_usage += (1 * 1000) / (
                                    self.ipc * self.frequency
                                )
                            # cache the instruction to the core
                            core.cache_instruction(instruction)
                            schedulable_instructions -= 1
                        # mode 2: assign as many instructions as possible to one core, then move on to the next core
                        elif self.mode == 2:
                            core = available_cores[0]
                            for _ in range(
                                round(
                                    min(
                                        [
                                            schedulable_instructions,
                                            core.computational_power.amount,
                                        ]
                                    )
                                )
                            ):
                                # get the next instruction
                                instruction = process.unscheduled_instructions.pop(0)
                                # update the host ram usage
                                if process.host is None:
                                    raise RuntimeError()
                                # a value error exception will be raised if fail to distribute the ram space
                                instruction.get(process.host.ram, instruction.length)
                                if process.container is not None:
                                    # update the container's ram usage
                                    process.container._ram_usage += instruction.length
                                    # break the loop if container's ram usage exceeds the limit
                                    if (
                                        process.container.ram_usage
                                        > process.container.ram_limit
                                    ):
                                        raise Exception()
                                    # update the container's cpu usage
                                    process.container._cpu_usage += (1 * 1000) / (
                                        self.ipc * self.frequency
                                    )
                                # cache the instruction to the core
                                core.cache_instruction(instruction)
                                schedulable_instructions -= 1
                except Exception:
                    process.fail(simulation.now)
                    if process.container is not None:
                        process.container.fail(simulation.now)
                    continue                   

    def on_power_off(self) -> None:
        """Power off the CPU, also terminates all unfinished processes."""
        # terminate all unfinished processes
        for process in self.process_queue:
            process.fail(simulation.now)

        # power off all the cores
        for core in self.cores:
            core.power_off(at=simulation.now)

        # cancel process scheduling
        for event in self.events:
            if event.label == f"{self} Scheduling process":
                event.cancel()

    def on_fail(self) -> None:
        self.power_off(simulation.now)
    
    @property
    def ipc(self) -> int:
        """Returns the number of instructions per cycle (IPC) of the CPU core."""
        return self._ipc

    @property
    def frequency(self) -> int:
        """Returns the frequency of the CPU core."""
        return self._frequency

    @property
    def num_cores(self) -> int:
        """Returns the number of CPU cores."""
        return self._num_cores

    @property
    def tdp(self) -> int | float:
        """Returns the thermal design power (TDP) of the CPU."""
        return self._tdp

    @property
    def computational_power_reservoir(self) -> Resource:
        """Returns the computational power reservoir of the CPU."""
        return self._computational_power_reservoir

    @property
    def process_queue(self):
        """Returns the process queue of the CPU."""
        return self._process_queue

    @property
    def cores(self):
        """Returns the cores of the CPU."""
        return self._cores

    @property
    def host(self):
        """Returns the host of the CPU."""
        return self._host

    @property
    def mode(self):
        """Returns the mode of the CPU."""
        return self._mode
    
    @property
    def instruction_cycle(self):
        """Returns the instruction cycle of the CPU."""
        return 1 / (self.ipc * self.frequency)

    def usage(self, duration: int | float | None = None):
        """Returns the CPU usage."""
        return sum([core.usage(duration) for core in self.cores])
    
    def utilization(self, duration: int | float | None = None):
        """Returns the CPU utilization."""
        return sum([core.utilization(duration) for core in self.cores]) / len(
            self.cores
        )
