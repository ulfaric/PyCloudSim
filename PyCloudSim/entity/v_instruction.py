from __future__ import annotations

from random import randbytes, randint
from typing import TYPE_CHECKING, Callable, List

from Akatosh import Entity
from Akatosh.entity import Entity

from PyCloudSim import logger, simulation

from .constants import Constants

if TYPE_CHECKING:
    from .v_process import vProcess, vContainerProcess, vDeamon, vDecoder


class vInstruction(Entity):
    """Base for simulated instructions."""

    def __init__(
        self,
        process: vProcess | vContainerProcess | vDeamon | vDecoder,
        create_at: int | float | Callable[..., int] | Callable[..., float] | None,
    ) -> None:
        """Create a simulated instruction. It will be consumed by the simulated CPU core. Once all simulated instruction of a process is consumed, the process is considered to be successfully executed."""
        super().__init__(f"{process.label}-{len(process.instructions)}", create_at)
        self._process = process
        self._instruction = bytes()

    def __str__(self) -> str:
        return f"{self.__class__.__name__}-{self.label}"

    def on_creation(self):
        """Populate the instruction with random bytes to simulate RAM usage."""
        if self.process.host is None:
            raise RuntimeError(f"{self} is not associated a host")

        if self.process.host.architecture == Constants.X86:
            self._instruction = randbytes(randint(1, 16))
        elif self.process.host.architecture == Constants.ARM:
            self._instruction = randbytes(4)
        else:
            raise RuntimeError(f"{self.process.host} has an unknown architecture")
        self.process.instructions.append(self)
        self.process.unscheduled_instructions.append(self)

    def on_termination(self):
        """Terminate the simulated instruction. Called when the instruction is consumed by the CPU core."""
        # clear out the resource usage
        if self.process.container is not None:
            if self.process.container.host is not None:
                self.process.container._cpu_usage -= (1 * 1000) / (
                    self.process.container.host.cpu.ipc
                    * self.process.container.host.cpu.frequency
                )
                self.process.container._ram_usage -= self.length

    @property
    def process(self):
        """Return the process that this instruction belongs to."""
        return self._process

    @property
    def instruction(self) -> bytes:
        """The instruction"""
        return self._instruction

    @property
    def length(self) -> int:
        """The length of the instruction"""
        return len(self.instruction) * 100000
