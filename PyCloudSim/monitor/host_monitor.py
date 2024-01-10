from __future__ import annotations

from typing import TYPE_CHECKING, Callable, List

from PyCloudSim import logger, simulation

from ..monitor import Monitor
import pandas as pd

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
                    f"{simulation.now}:\t{host} CPU usage: {host.cpu_utilization(self.sample_period)*100:.2f}% , RAM usage: {host.ram_utilization(self.sample_period)*100:.2f}%, BW-Out usage: {host.NIC.egress_usage(self.sample_period):.2f}%, BW-In usage: {host.NIC.ingress_usage(self.sample_period):.2f}%"
                )

    @property
    def target_hosts(self):
        """The target hosts of the monitor."""
        return self._target_hosts


class DataframeHostMonitor(Monitor):
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

        self._dataframe = pd.DataFrame(
            {
                "time": pd.Series([], dtype="str"),
                "host_label": pd.Series([], dtype="str"),
                "cpu_usage": pd.Series([], dtype="float"),
                "cpu_usage_percent": pd.Series([], dtype="float"),
                "ram_usage": pd.Series([], dtype="float"),
                "ram_usage_percent": pd.Series([], dtype="float"),
                "rom_usage": pd.Series([], dtype="float"),
                "rom_usage_percent": pd.Series([], dtype="float"),
                "bandwidth_usage": pd.Series([], dtype="float"),
                "ingress_usage": pd.Series([], dtype="float"),
                "ingress_usage_percent": pd.Series([], dtype="float"),
                "egress_usage": pd.Series([], dtype="float"),
                "egress_usage_percent": pd.Series([], dtype="float"),
            }
        )

    def on_observation(self, *arg, **kwargs):
        for host in self.target_hosts:
            host_telemetries = pd.DataFrame(
                {
                    "time": pd.Series([simulation.now], dtype="str"),
                    "host_label": pd.Series([host.label], dtype="str"),
                    "cpu_usage": pd.Series(
                        [host.cpu_usage(self.sample_period)], dtype="float"
                    ),
                    "cpu_usage_percent": pd.Series(
                        [host.cpu_utilization(self.sample_period) * 100], dtype="float"
                    ),
                    "ram_usage": pd.Series(
                        [host.ram_usage(self.sample_period)], dtype="float"
                    ),
                    "ram_usage_percent": pd.Series(
                        [host.ram_utilization(self.sample_period) * 100], dtype="float"
                    ),
                    "rom_usage": pd.Series(
                        [host.rom.usage(self.sample_period)], dtype="float"
                    ),
                    "rom_usage_percent": pd.Series(
                        [host.rom.utilization(self.sample_period) * 100], dtype="float"
                    ),
                    "bandwidth_usage": pd.Series(
                        [host.NIC.egress_usage(self.sample_period)], dtype="float"
                    ),
                    "ingress_usage": pd.Series(
                        [host.NIC.ingress_usage(self.sample_period)], dtype="float"
                    ),
                    "ingress_usage_percent": pd.Series(
                        [host.NIC.ingress_utilization(self.sample_period) * 100],
                        dtype="float",
                    ),
                    "egress_usage": pd.Series(
                        [host.NIC.egress_usage(self.sample_period)], dtype="float"
                    ),
                    "egress_usage_percent": pd.Series(
                        [host.NIC.egress_utilization(self.sample_period) * 100],
                        dtype="float",
                    ),
                }
            )
            self._dataframe = pd.concat(
                [self._dataframe, host_telemetries], ignore_index=True
            )

    @property
    def target_hosts(self):
        """The target hosts of the monitor."""
        return self._target_hosts

    @property
    def dataframe(self):
        """Return the dataframe of the monitor."""
        return self._dataframe
