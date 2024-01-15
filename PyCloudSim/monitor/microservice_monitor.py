from __future__ import annotations

from typing import TYPE_CHECKING, Callable, List

from PyCloudSim import logger, simulation

from ..monitor import Monitor

import pandas as pd

if TYPE_CHECKING:
    from ..entity import vMicroservice


class LoggingMicroserviceMonitor(Monitor):
    def __init__(
        self,
        label: str,
        targeted_microservices: List[vMicroservice] | None = None,
        sample_period: int | float | Callable[..., int] | Callable[..., float] = 0.1,
    ) -> None:
        super().__init__(label, sample_period)
        if targeted_microservices is None:
            self._targeted_microservices = simulation.microservices
        else:
            self._targeted_microservices = targeted_microservices

    def on_observation(self, *arg, **kwargs):
        """Simply log the CPU and RAM usage of the containers."""
        for microservice in self.targeted_microservices:
            logger.info(
                f"{simulation.now}:\t{microservice} CPU usage: {microservice.cpu_utilization*100:.2f}% , RAM usage: {microservice.ram_utilization*100:.2f}%"
            )

    @property
    def targeted_microservices(self):
        """Return the target containers of the monitor."""
        return self._targeted_microservices


class DataframeMicroserviceMonitor(Monitor):
    def __init__(
        self,
        label: str,
        targeted_microservices: List[vMicroservice] | None = None,
        sample_period: int | float | Callable[..., int] | Callable[..., float] = 0.1,
    ) -> None:
        super().__init__(label, sample_period)
        if targeted_microservices is None:
            self._targeted_microservices = simulation.microservices
        else:
            self._targeted_microservices = targeted_microservices

        self._dataframe = pd.DataFrame({
            "time": pd.Series(dtype="float64"),
            "microservice": pd.Series(dtype="string"),
            "cpu_usage": pd.Series(dtype="float64"),
            "ram_usage": pd.Series(dtype="float64"),
            "num_containers": pd.Series(dtype="int64"),
        })
        
    def on_observation(self, *arg, **kwargs):
        """Simply log the CPU and RAM usage of the containers."""
        for microservice in self.targeted_microservices:
            microservice_telemetries = pd.DataFrame({
                "time": pd.Series([simulation.now], dtype="float64"),
                "microservice": pd.Series([microservice.label], dtype="string"),
                "cpu_usage": pd.Series([microservice.cpu_utilization], dtype="float64"),
                "ram_usage": pd.Series([microservice.ram_utilization], dtype="float64"),
                "num_containers": pd.Series([microservice.num_active_containers], dtype="int64"),
            })
            self._dataframe = pd.concat([self._dataframe, microservice_telemetries], ignore_index=True)
                
    @property
    def dataframe(self):
        return self._dataframe
    
    @property
    def targeted_microservices(self):
        """Return the target containers of the monitor."""
        return self._targeted_microservices
        