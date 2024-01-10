from __future__ import annotations

from typing import TYPE_CHECKING, Callable, List

from PyCloudSim import logger, simulation

from ..monitor import Monitor

import pandas as pd

if TYPE_CHECKING:
    from ..entity import vContainer


class LoggingContainerMonitor(Monitor):
    """A default container monitor that will simply log the CPU and RAM usage of the containers.
    """
    def __init__(
        self,
        label: str,
        target_containers: List[vContainer] | None = None,
        sample_period: int | float | Callable[..., int] | Callable[..., float] = 0.1,
    ) -> None:
        """Initialize the LoggingContainerMonitor.

        Args:
            label (str): short name of the monitor.
            target_containers (List[vContainer] | None, optional): the container to be monitored. Defaults to None then all containers will be monitored.
            sample_period (int | float | Callable[..., int] | Callable[..., float], optional): the sampling period. Defaults to 0.1.
        """
        super().__init__(label, sample_period)

        if target_containers is None:
            self._target_containers = simulation.containers
        else:
            self._target_containers = target_containers

    def on_observation(self, *arg, **kwargs):
        """Simply log the CPU and RAM usage of the containers.
        """
        for container in self.target_containers:
            if container.initiated:
                logger.info(
                    f"{simulation.now}:\t{container} CPU usage: {container.cpu_usage/container.cpu_limit*100:.2f}% , RAM usage: {container.ram_usage/container.ram_limit*100:.2f}%"
                )

    @property
    def target_containers(self):
        """Return the target containers of the monitor."""
        return self._target_containers

class DataframeContainerMonitor(Monitor):
    """A simple monitor that will log the CPU and RAM usage of the containers in a dataframe."""
    def __init__(
        self,
        label: str,
        target_containers: List[vContainer] | None = None,
        sample_period: int | float | Callable[..., int] | Callable[..., float] = 0.1,
    ) -> None:
        """Initialize the LoggingContainerMonitor.

        Args:
            label (str): short name of the monitor.
            target_containers (List[vContainer] | None, optional): the container to be monitored. Defaults to None then all containers will be monitored.
            sample_period (int | float | Callable[..., int] | Callable[..., float], optional): the sampling period. Defaults to 0.1.
        """
        super().__init__(label, sample_period)

        if target_containers is None:
            self._target_containers = simulation.containers
        else:
            self._target_containers = target_containers
            
        self._dataframe = pd.DataFrame({
            "time": pd.Series([], dtype="str"),
            "container_label": pd.Series([], dtype="str"),
            "cpu_usage": pd.Series([], dtype="float"),
            "cpu_usage_percent": pd.Series([], dtype="float"),
            "ram_usage": pd.Series([], dtype="float"),
            "ram_usage_percent": pd.Series([], dtype="float"),
            "num_of_process": pd.Series([], dtype="int"),
        })

    def on_observation(self, *arg, **kwargs):
        for container in self.target_containers:
            if container.initiated:
                container_telemetries = pd.DataFrame(
                    {
                        "time": pd.Series([simulation.now], dtype="str"),
                        "container_label": pd.Series([container.label], dtype="str"),
                        "cpu_usage": pd.Series([container.cpu_usage], dtype="float"),
                        "cpu_usage_percent": pd.Series([container.cpu_usage/container.cpu_limit*100], dtype="float"),
                        "ram_usage": pd.Series([container.ram_usage], dtype="float"),
                        "ram_usage_percent": pd.Series([container.ram_usage/container.ram_limit*100], dtype="float"),
                        "num_of_process": pd.Series([len(container.process_queue)], dtype="int"),
                    }
                )
                self._dataframe = pd.concat([self._dataframe, container_telemetries], ignore_index=True)


    @property
    def target_containers(self):
        """Return the target containers of the monitor."""
        return self._target_containers
    
    @property
    def dataframe(self):
        """Return the dataframe of the monitor."""
        return self._dataframe

