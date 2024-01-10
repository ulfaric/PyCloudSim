from __future__ import annotations

from abc import ABC, abstractmethod
from math import inf
from random import choice
from typing import Callable, List, Tuple

from Akatosh import Entity, EntityList
from networkx import volume

from PyCloudSim import logger, simulation
from PyCloudSim.entity.constants import Constants

from .v_container import vContainer
from .v_sofware_entity import vSoftwareEntity


class vLoadbalancer(ABC):
    """Base class for loadbalancers."""

    def __init__(self) -> None:
        pass

    @abstractmethod
    def getContainer(self, ms: vMicroservice) -> vContainer:
        """Return the next container to be used."""
        pass


class Random(vLoadbalancer):
    """A loadbalancer that randomly select a container instance."""

    def __init__(self) -> None:
        super().__init__()

    def getContainer(self, ms: vMicroservice):
        container = choice(
            [container for container in ms.containers if container.initiated]
        )
        logger.info(f"{simulation.now}:\t{ms} selected {container}")
        return container


class Bestfit(vLoadbalancer):
    """A loadbalancer that selects the container instance with the most CPU and RAM usage."""

    def __init__(self) -> None:
        super().__init__()

    def getContainer(self, ms: vMicroservice):
        ms.containers.sort(key=lambda container: container.cpu_usage)
        ms.containers.sort(key=lambda container: container.ram_usage)
        container = [container for container in ms.containers if container.initiated][
            -1
        ]
        logger.info(f"{simulation.now}:\t{ms} selected {container}")
        return container


class Worstfit(vLoadbalancer):
    """A loadbalancer that selects the container instance with the least CPU and RAM usage."""

    def __init__(self) -> None:
        super().__init__()

    def getContainer(self, ms: vMicroservice):
        ms.containers.sort(key=lambda container: container.cpu_usage)
        ms.containers.sort(key=lambda container: container.ram_usage)
        container = [container for container in ms.containers if container.initiated][0]
        logger.info(f"{simulation.now}:\t{ms} selected {container}")
        return container


class vMicroservice(vSoftwareEntity, ABC):
    def __init__(
        self,
        cpu: int | Callable[..., int],
        ram: int | Callable[..., int],
        image_size: int | Callable[..., int],
        cpu_limit: int | Callable[..., int] | None = None,
        ram_limit: int | Callable[..., int] | None = None,
        volumes: List[Tuple[int, str, str]] = [],
        priority: int | Callable[..., int] = 0,
        deamon: bool | Callable[..., bool] = False,
        min_num_instances: int | Callable[..., int] = 1,
        max_num_instances: int | Callable[..., int] = 3,
        loadbalancer: vLoadbalancer = Bestfit(),
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
        """Base for simulated microservices. It includes the horizontal scaling functionality."""
        super().__init__(label, create_at, terminate_at, precursor)

        self._cpu = cpu
        self._ram = ram
        self._image_size = image_size
        self._cpu_limit = cpu_limit
        self._ram_limit = ram_limit
        self._volume_descriptions = volumes
        self._priority = priority
        self._demmon = deamon
        self._scaling = False

        if callable(min_num_instances):
            self._min_num_instances = round(min_num_instances())
        else:
            self._min_num_instances = min_num_instances

        if callable(max_num_instances):
            self._max_num_instances = round(max_num_instances())
        else:
            self._max_num_instances = max_num_instances

        self._containers: List[vContainer] = EntityList(label=f"{self} Containers")

        self._loadbalancer = loadbalancer

        for _ in range(self._min_num_instances):
            self.containers.append(
                vContainer(
                    self.cpu,
                    self.ram,
                    self.image_size,
                    self.cpu_limit,
                    self.ram_limit,
                    self.volume_descriptions,
                    self.priority,
                    self.deamon,
                    label=f"{self.label}-{len(self._containers)}",
                )
            )

    def horizontal_scale_up(self, num_instances: int, at: int | float):
        """Horizontal scale up the microservice by adding new container instances."""

        if self.scaling:
            return

        self._scaling = True

        @self.instant_event(at, label=f"{self} Horizontal Scale Up", priority=-1)
        def _scale_up():
            for _ in range(num_instances):
                self.containers.append(
                    vContainer(
                        self.cpu,
                        self.ram,
                        self.image_size,
                        self.cpu_limit,
                        self.ram_limit,
                        self.volume_descriptions,
                        self.priority,
                        self.deamon,
                        label=f"{self.label}-{len(self._containers)}",
                        create_at=simulation.now,
                    )
                )
            self._scaling = False

    def horizontal_scale_down(self, num_instances: int, at: int | float):
        """Horizontal scale down the microservice by terminating container instances. This can not cause the number of container instances to be less than the minimum number of instances."""
        if self.scaling:
            return

        self._scaling = True

        @self.instant_event(at, label=f"{self} Horizontal Scale Down", priority=-1)
        def _scale_down():
            for i in range(
                min([num_instances, len(self.containers) - self.min_num_instances])
            ):
                self.containers[i].terminate(simulation.now)

    def vertical_scale(
        self,
        at: int | float,
        cpu: int | Callable[..., int],
        ram: int | Callable[..., int],
        image_size: int | Callable[..., int],
        cpu_limit: int | Callable[..., int] | None = None,
        ram_limit: int | Callable[..., int] | None = None,
        init_delay: int | float | Callable[..., int] | Callable[..., float] = 0,
        priority: int | Callable[..., int] = 0,
        deamon: bool | Callable[..., bool] = False,
        min_num_instances: int | Callable[..., int] = 1,
        max_num_instances: int | Callable[..., int] = 3,
        evaluation_interval: int
        | float
        | Callable[..., int]
        | Callable[..., float] = 0.1,
        cpu_upper_threshold: float | Callable[..., float] = 0.8,
        cpu_lower_threshold: float | Callable[..., float] = 0.2,
        ram_upper_threshold: float | Callable[..., float] = 0.8,
        ram_lower_threshold: float | Callable[..., float] = 0.2,
    ):
        """Scaling the microservice vertically by changing the attributes of the microservice. This will terminate all the current container instances and create new container instances with the new attributes."""

        @self.instant_event(at, label=f"{self} Vertical Scale", priority=-1)
        def _vertical_scale():
            # update the attributes
            self._cpu = cpu
            self._ram = ram
            self._image_size = image_size
            self._cpu_limit = cpu_limit
            self._ram_limit = ram_limit
            self._priority = priority
            self._demmon = deamon
            self._scaling = False

            if callable(min_num_instances):
                self._min_num_instances = round(min_num_instances())
            else:
                self._min_num_instances = min_num_instances

            if callable(max_num_instances):
                self._max_num_instances = round(max_num_instances())
            else:
                self._max_num_instances = max_num_instances

            # record the current number of instances
            number_instance = len(self.containers)
            # terminate all the current instances
            for container in self.containers:
                container.terminate(simulation.now)
            # create new instances
            for _ in range(number_instance):
                self.containers.append(
                    vContainer(
                        self.cpu,
                        self.ram,
                        self.image_size,
                        self.cpu_limit,
                        self.ram_limit,
                        self.volume_descriptions,
                        self.priority,
                        self.deamon,
                        label=f"{self.label}-{len(self._containers)}",
                        create_at=simulation.now,
                    )
                )

    @abstractmethod
    def horizontal_scale_up_triggered(self) -> bool:
        """Abstract method for evaluating if the microservice should be scaled up horizontally."""
        pass

    @abstractmethod
    def horizontal_scale_down_triggered(self) -> bool:
        """Abstract method for evaluating if the microservice should be scaled down horizontally."""
        pass

    def getContainer(self):
        """Get the container instance according to the loadbalancer."""
        return self.loadbalancer.getContainer(self)

    def on_creation(self):
        """Creation procedure of the microservice. It will create the container instances and the evaluator."""
        for container in self._containers:
            container.create(simulation.now)

        @self.continuous_event(
            at=simulation.now,
            interval=simulation.min_time_unit,
            duration=inf,
            label=f"{self} Evaluator",
        )
        def _evaluator():
            initiated_containers = [
                container for container in self._containers if container.initiated
            ]
            # check if the microservice is ready
            if len(initiated_containers) < self.min_num_instances:
                if self.ready:
                    self.state.remove(Constants.READY)
                    for _ in range(self.min_num_instances - len(initiated_containers)):
                        self.containers.append(
                            vContainer(
                                self.cpu,
                                self.ram,
                                self.image_size,
                                self.cpu_limit,
                                self.ram_limit,
                                self.volume_descriptions,
                                self.priority,
                                self.deamon,
                                label=f"{self.label}-{len(self._containers)}",
                                create_at=simulation.now,
                            )
                        )
                    logger.info(f"{simulation.now}:\t{self} is not ready, recreating {self.min_num_instances - len(initiated_containers)} container instances")
                return
            else:
                if not self.ready:
                    self.state.append(Constants.READY)
                    logger.info(f"{simulation.now}:\t{self} is ready")

            # check if any container instance is pending:
            if len(initiated_containers) != len(self.containers):
                # if any instance is pending, skip the scaling evaluation
                return

            # check if the microservice should be scaled up
            if len(self.containers) < self.max_num_instances:
                if self.horizontal_scale_up_triggered():
                    self.horizontal_scale_up(1, simulation.now)
                    return

            # check if the microservice should be scaled down
            if len(self.containers) > self.min_num_instances:
                if self.horizontal_scale_down_triggered():
                    self.horizontal_scale_down(1, simulation.now)
                    return

    def on_termination(self):
        for container in self._containers:
            container.terminate(simulation.now)

    @property
    def cpu(self):
        """Return the required CPU time for each container instance."""
        return self._cpu

    @property
    def ram(self):
        """Return the required RAM for each container instance."""
        return self._ram

    @property
    def image_size(self):
        """Return the image size for each container instance."""
        return self._image_size

    @property
    def cpu_limit(self):
        """Return the CPU limit for each container instance."""
        return self._cpu_limit

    @property
    def ram_limit(self):
        """Return the RAM limit for each container instance."""
        return self._ram_limit

    @property
    def priority(self):
        """Return the priority for each container instance."""
        return self._priority

    @property
    def deamon(self):
        """Return the deamon flag for each container instance."""
        return self._demmon

    @property
    def min_num_instances(self):
        """Return the minimum number of container instances."""
        return self._min_num_instances

    @property
    def max_num_instances(self):
        """Return the maximum number of container instances."""
        return self._max_num_instances

    @property
    def containers(self):
        """Return the list of container instances."""
        return self._containers

    @property
    def cpu_usage(self):
        """Return the overall CPU usage of the microservice."""
        return sum(
            container.cpu_usage for container in self._containers if container.initiated
        )

    @property
    def cpu_utilization(self):
        """Return the overall CPU utilization of the microservice."""
        return sum(
            container.cpu_utilization
            for container in self._containers
            if container.initiated
        ) / len(self.containers)

    @property
    def ram_usage(self):
        """Return the overall RAM usage of the microservice."""
        return sum(
            container.ram_usage for container in self._containers if container.initiated
        )

    @property
    def ram_utilization(self):
        """Return the overall RAM utilization of the microservice."""
        return sum(
            container.ram_utilization
            for container in self._containers
            if container.initiated
        ) / len(self.containers)

    @property
    def scaling(self):
        """Return true if the microservice is scaling up or down."""
        return self._scaling

    @property
    def ready(self):
        """Return true if the microservice is ready."""
        return Constants.READY in self.state

    @property
    def loadbalancer(self):
        """Return the loadbalancer of the microservice."""
        return self._loadbalancer
    
    @property
    def volume_descriptions(self):
        """Return the volume descriptions of the microservice."""
        return self._volume_descriptions


class vDefaultMicroservice(vMicroservice):
    def __init__(
        self,
        cpu: int | Callable[..., int],
        ram: int | Callable[..., int],
        image_size: int | Callable[..., int],
        cpu_limit: int | Callable[..., int] | None = None,
        ram_limit: int | Callable[..., int] | None = None,
        volumes: List[Tuple[int, str, str]] = [],
        priority: int | Callable[..., int] = 0,
        deamon: bool | Callable[..., bool] = False,
        min_num_instances: int | Callable[..., int] = 1,
        max_num_instances: int | Callable[..., int] = 3,
        loadbalancer: vLoadbalancer = Bestfit(),
        evaluation_interval: int
        | float
        | Callable[..., int]
        | Callable[..., float] = 0.1,
        cpu_upper_threshold: float | Callable[..., float] = 0.8,
        cpu_lower_threshold: float | Callable[..., float] = 0.2,
        ram_upper_threshold: float | Callable[..., float] = 0.8,
        ram_lower_threshold: float | Callable[..., float] = 0.2,
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
        """Default microservice. It will scale up if CPU or RAM utilization reached upper threshold. It will scale down if CPU and RAM utilization reached lower threshold."""
        super().__init__(
            cpu,
            ram,
            image_size,
            cpu_limit,
            ram_limit,
            volumes,
            priority,
            deamon,
            min_num_instances,
            max_num_instances,
            loadbalancer,
            label,
            create_at,
            terminate_at,
            precursor,
        )

        if callable(cpu_upper_threshold):
            self._cpu_upper_threshold = cpu_upper_threshold()
        else:
            self._cpu_upper_threshold = cpu_upper_threshold

        if callable(cpu_lower_threshold):
            self._cpu_lower_threshold = cpu_lower_threshold()
        else:
            self._cpu_lower_threshold = cpu_lower_threshold

        if callable(ram_upper_threshold):
            self._ram_upper_threshold = ram_upper_threshold()
        else:
            self._ram_upper_threshold = ram_upper_threshold

        if callable(ram_lower_threshold):
            self._ram_lower_threshold = ram_lower_threshold()
        else:
            self._ram_lower_threshold = ram_lower_threshold

    def horizontal_scale_up_triggered(self) -> bool:
        """The microservice will be scaled up if CPU or RAM utilization reached upper threshold."""
        if (
            self.cpu_utilization >= self.cpu_upper_threshold
            or self.ram_utilization >= self.ram_upper_threshold
        ):
            return True
        else:
            return False

    def horizontal_scale_down_triggered(self) -> bool:
        """The microservice will be scaled down if CPU and RAM utilization reached lower threshold."""
        if (
            self.cpu_utilization <= self.cpu_lower_threshold
            and self.ram_utilization <= self.ram_lower_threshold
        ):
            return True
        else:
            return False

    @property
    def cpu_upper_threshold(self):
        """Return the CPU upper threshold. If CPU utilization reached this threshold, the microservice will be scaled up."""
        return self._cpu_upper_threshold

    @property
    def cpu_lower_threshold(self):
        """Return the CPU lower threshold. If CPU utilization reached this threshold, the microservice will be scaled down (if RAM utilization also reached lower threshold)."""
        return self._cpu_lower_threshold

    @property
    def ram_upper_threshold(self):
        """Return the RAM upper threshold. If RAM utilization reached this threshold, the microservice will be scaled up."""
        return self._ram_upper_threshold

    @property
    def ram_lower_threshold(self):
        """Return the RAM lower threshold. If RAM utilization reached this threshold, the microservice will be scaled down (if CPU utilization also reached lower threshold)."""
        return self._ram_lower_threshold
