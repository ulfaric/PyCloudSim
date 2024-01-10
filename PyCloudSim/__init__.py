from __future__ import annotations

import logging
from ipaddress import ip_address
from math import inf
from typing import TYPE_CHECKING, List

from Akatosh import Entity, EntityList, Mundus

if TYPE_CHECKING:
    from .entity import (
        vContainer,
        vHost,
        vHardwareEntity,
        vPacket,
        vSwitch,
        vGateway,
        vVolume,
        vAPICall,
    )
    from .scheduler import ContainerScheduler, VolumeScheduler

import matplotlib.pyplot as plt
import networkx as nx
from Akatosh import EntityList
from bitmath import MiB
from networkx.drawing.layout import spring_layout
from networkx.drawing.nx_pylab import (
    draw_networkx_edges,
    draw_networkx_labels,
    draw_networkx_nodes,
)


class vNetwork:
    def __init__(self) -> None:
        self._topology = nx.DiGraph()
        self._nodes: List[vHardwareEntity] = EntityList()

    def add_node(self, node: vHardwareEntity) -> None:
        """Adds a node to the network."""
        self.topology.add_node(node)
        self.nodes.append(node)

    def del_node(self, node: vHardwareEntity) -> None:
        """Removes a node from the network."""
        self.topology.remove_node(node)
        self.nodes.remove(node)

    def add_link(
        self,
        s: vHardwareEntity | vHost | vSwitch | vGateway,
        d: vHardwareEntity | vHost | vSwitch | vGateway,
        bandwidth: int,
        at: int | float = 0,
    ) -> None:
        """Adds a link between two nodes."""

        if s.__class__.__name__ == "vHost" and d.__class__.__name__ == "vHost":
            raise ValueError("Cannot add a link between two hosts.")

        self.topology.add_weighted_edges_from(
            [(s, d, MiB(bandwidth).bytes), (d, s, MiB(bandwidth).bytes)]
        )
        if s.__class__.__name__ != "vSwitch":
            ip_address = d.available_ip_addresses.pop(0)  # type: ignore
            s.NIC.add_port(d, bandwidth, ip_address, at)
        else:
            s.NIC.add_port(d, bandwidth, ip_address=None, at=at)

        if d.__class__.__name__ != "vSwitch":
            ip_address = s.available_ip_addresses.pop(0)  # type: ignore
            d.NIC.add_port(s, bandwidth, ip_address, at)
        else:
            d.NIC.add_port(s, bandwidth, None, at)

    def remove_link(
        self, s: vHardwareEntity, d: vHardwareEntity, at: int | float = 0
    ) -> None:
        """Removes a link between two nodes."""
        self.topology.remove_edge(s, d)
        self.topology.remove_edge(d, s)
        s.NIC.remove_port(d, at)
        d.NIC.remove_port(s, at)

    def plot(self, file_name: str = "topology.png") -> None:
        """Plots the network topology."""
        fig, ax = plt.subplots()
        label_mapping = dict()
        for node in self.nodes:
            label_mapping[node] = node
        pos = spring_layout(self.topology)
        for node in self.topology.nodes:
            if node.__class__.__name__ == "vHost":
                draw_networkx_nodes(
                    self.topology, pos, ax=ax, nodelist=[node], node_color="tab:green"
                )
            if node.__class__.__name__ == "vSwitch":
                draw_networkx_nodes(
                    self.topology, pos, ax=ax, nodelist=[node], node_color="tab:blue"
                )
            if node.__class__.__name__ == "vRouter":
                draw_networkx_nodes(
                    self.topology, pos, ax=ax, nodelist=[node], node_color="tab:orange"
                )
        for edge in self.topology.edges:
            draw_networkx_edges(
                self.topology, pos, ax=ax, edgelist=[edge], edge_color="tab:gray"
            )
        draw_networkx_labels(self.topology, pos, labels=label_mapping, ax=ax)
        fig.savefig(file_name)

    def route(self, src: vHost | vGateway, dst: vHost | vGateway):
        """Returns a list of nodes the packet will traverse."""
        return nx.shortest_path(self.topology, src, dst)

    @property
    def topology(self):
        "Returns the network topology as a networkx directional graph."
        return self._topology

    @property
    def nodes(self):
        """Returns a list of all hosts in the network."""
        return self._nodes


logger = logging.getLogger("PyCloudSim")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s\t%(levelname)s\t%(message)s")

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

file_handler = logging.FileHandler(filename=".log", mode="w")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class APICallScheduler(Entity):
    """Base for all container schedulers."""

    def __init__(self) -> None:
        super().__init__(label="Volume Scheduler", create_at=0, precursor=None)

    def on_creation(self):
        super().on_creation()

        @self.continuous_event(
            at=simulation.now,
            interval=simulation.min_time_unit,
            duration=inf,
            label="Scheduling API Calls",
            priority=inf,
        )
        def scheduling():
            uninitiated_api_calls = [
                api_call
                for api_call in simulation.api_calls
                if not api_call.initiated and api_call.created
            ]
            for api_call in uninitiated_api_calls:
                src_ready = True
                if api_call.src.__class__.__name__ == "vMicroservice":
                    src_ready = api_call.src.ready  # type: ignore

                dst_ready = True
                if api_call.dst.__class__.__name__ == "vMicroservice":
                    dst_ready = api_call.dst.ready  # type: ignore

                if src_ready and dst_ready:
                    api_call.initiate(simulation.now)

    def on_termination(self):
        return super().on_termination()

    def on_destruction(self):
        return super().on_destruction()


class Simulation:
    def __init__(self) -> None:
        self._containers: List[vContainer] = EntityList(label="Containers")
        self._volumes: List[vVolume] = EntityList(label="Volumes")
        self._api_calls: List[vAPICall] = EntityList(label="APICalls")
        self._network = vNetwork()

        self._container_scheduler: ContainerScheduler = None  # type: ignore
        self._volume_scheduler: VolumeScheduler = None  # type: ignore
        self._api_call_scheduler: APICallScheduler = APICallScheduler()

        self._resolution = 4
        Mundus.resolution = self.resolution

    def simulate(self, until: int | float | None = None):
        Mundus.simulate(until)

    def debug(self, enable: bool = True):
        if enable:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

    def set_resolution(self, resolution: int):
        self._resolution = resolution
        Mundus.resolution = self.resolution

    @property
    def hosts(self) -> List[vHost]:
        return [
            host for host in self.topology.nodes if host.__class__.__name__ == "vHost"
        ]

    @property
    def network(self):
        return self._network

    @property
    def topology(self):
        return self.network.topology

    @property
    def containers(self):
        return self._containers

    @property
    def volumes(self):
        return self._volumes

    @property
    def api_calls(self):
        return self._api_calls

    @property
    def now(self):
        return Mundus.now

    @property
    def resolution(self):
        return self._resolution

    @property
    def container_scheduler(self):
        if self._container_scheduler is None:
            raise ValueError("Container scheduler is not set")
        return self._container_scheduler

    @property
    def volume_scheduler(self):
        if self._volume_scheduler is None:
            raise ValueError("Volume scheduler is not set")
        return self._volume_scheduler

    @property
    def min_time_unit(self):
        return round(1 / pow(10, self.resolution), self.resolution)


simulation = Simulation()
