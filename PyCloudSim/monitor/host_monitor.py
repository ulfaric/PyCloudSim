from __future__ import annotations

from typing import TYPE_CHECKING, Callable, List

from PyCloudSim import logger, simulation

from ..monitor import Monitor

if TYPE_CHECKING:
    from ..entity import vHost


class LoggingHostMonitor(Monitor):
    """A default host monitor that will simply log the CPU and RAM usage of the hosts."""

    def __init__(
        self,
        label: str,
        target_hosts: List[vHost] | None = None,
        sample_period: int | float | Callable[..., int] | Callable[..., float] = 0.1,
    ) -> None:
        """Initialize the LoggingHostMonitor.

        Args:
            label (str): short name of the monitor.
            target_hosts (List[vHost] | None, optional): the hosts to be monitored. Defaults to None then all hosts will be monitored.
            sample_period (int | float | Callable[..., int] | Callable[..., float], optional): the sampling frequency. Defaults to 0.1.
        """
        super().__init__(label, sample_period)

        if target_hosts is None:
            self._target_hosts = simulation.hosts
        else:
            self._target_hosts = target_hosts

    def on_observation(self, *arg, **kwargs):
        for host in self.target_hosts:
            if host.powered_on:
                logger.info(
                    f"{simulation.now}:\t{host} CPU usage: {host.cpu_utilization(self.sample_period)*100:.2f}% , RAM usage: {host.ram_utilization(self.sample_period)*100:.2f}%"
                )

    @property
    def target_hosts(self):
        """The target hosts of the monitor."""
        return self._target_hosts
