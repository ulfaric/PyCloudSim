from __future__ import annotations

from math import inf
from typing import Any, Callable, List

from Akatosh import Entity, EntityList, Event, Resource
from Akatosh.entity import Entity

from PyCloudSim import logger, simulation

from .v_hardware_component import vHardwareComponent
from .v_process import vInstruction, vProcess


class vCPUCore(vHardwareComponent):
    def __init__(
        self,
        ipc: int | Callable,
        frequency: int | Callable,
        label: str | None = None,
        create_at: int | float | Callable[..., Any] | None = None,
        terminate_at: int | float | Callable[..., Any] | None = None,
        precursor: Entity | List[Entity] | None = None,
    ) -> None:
        """Create a simulated CPU core.

        Args:
            ipc (int | Callable): instructions per cycle.
            frequency (int | Callable): the frequency of the CPU core.
            label (str | None, optional): the short description of the CPU Core. Defaults to None.
            create_at (int | float | Callable[..., Any] | None, optional): when this CPU core should be created. Defaults to None.
            terminate_at (int | float | Callable[..., Any] | None, optional): when this CPU core should be terminated. Defaults to None.
            precursor (Entity | List[Entity] | None, optional): the entity that this CPU core must not be created before. Defaults to None.
        """
        super().__init__(label, create_at, terminate_at, precursor)

        if callable(ipc):
            self._ipc = round(ipc())
        else:
            self._ipc = ipc

        if callable(frequency):
            self._frequency = round(frequency())
        else:
            self._frequency = frequency
        self._instruction_cycle = 1 / (self._ipc * self._frequency)
        self._computational_power = Resource(
            capacity=self.ipc * self.frequency,
            label=f"{self} Computational Power",
        )
        self._instructions_queue: List[vInstruction] = EntityList(
            label=f"{self} InstructionsQueue"
        )
        self._clock: Event = None  # type: ignore

    def on_power_on(self):
        """Create the execution clock of the CPU core."""

        @self.continuous_event(
            at=simulation.now + self.instruction_cycle,
            interval=self.instruction_cycle,
            duration=inf,
            label=f"{self.label} Clock",
        )
        def _execute_instruction():
            if len(self.instructions_queue) > 0:
                instruction = self.instructions_queue[0]
                instruction.terminate(at=simulation.now)
                logger.debug(
                    f"{simulation.now}:\t{self} executed {instruction}, current capacity: {self.computational_power.amount}, queue length: {len(self.instructions_queue)}."
                )
                if instruction.process.deamon:
                    instruction = vInstruction(
                        process=instruction.process,
                        create_at=simulation.now,
                    )

    def cache_instruction(self, instruction: vInstruction) -> None:
        """Cache instructions from a process to the CPU core."""
        self.instructions_queue.append(instruction)
        instruction.get(self.computational_power, 1)

    def on_power_off(self) -> None:
        """Power off the CPU core."""
        # terminate the clock of the CPU core.
        for event in self.events:
            if event.label == f"{self.label} Clock":
                event.cancel()

        # find impacted process.
        impacted_process: List[vProcess] = []
        for instruction in self.instructions_queue:
            if instruction.process not in impacted_process:
                impacted_process.append(instruction.process)
        # fail impacted process.
        for process in impacted_process:
            process.fail(simulation.now)

    def on_fail(self) -> None:
        self.power_off(simulation.now)

    @property
    def ipc(self) -> int:
        """Returns the number of instructions per cycle of the CPU core."""
        return self._ipc

    @property
    def frequency(self) -> int:
        """Returns the frequency of the CPU core."""
        return self._frequency

    @property
    def instruction_cycle(self) -> float:
        """Returns the time taken to execute one instruction."""
        return self._instruction_cycle

    @property
    def instructions_queue(self):
        """Returns the instructions queue of the CPU core."""
        return self._instructions_queue

    @property
    def computational_power(self) -> Resource:
        """Returns the computational power of the CPU core."""
        return self._computational_power

    @property
    def clock(self):
        """Returns the clock of the CPU core, which is the continuous event that consumes instructions."""
        return self._clock

    def usage(self, duration: int | float | None = None):
        """Returns the usage of the CPU core."""
        return self.computational_power.usage(duration)

    def utilization(self, duration: int | float | None = None):
        """Returns the utilization of the CPU core."""
        return self.computational_power.utilization(duration)
