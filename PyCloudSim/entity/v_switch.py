from __future__ import annotations

from ipaddress import IPv4Address, IPv4Network
from typing import Any, Callable, List

from Akatosh import Entity
from Akatosh.entity import Entity

from PyCloudSim.entity.constants import Constants

from .constants import Constants
from .v_hardware_entity import vHardwareEntity


class vSwitch(vHardwareEntity):
    def __init__(
        self,
        ipc: int | Callable[..., Any],
        frequency: int | Callable[..., Any],
        num_cores: int | Callable[..., Any],
        cpu_tdps: int | float | Callable[..., Any],
        cpu_mode: int,
        ram: int | Callable[..., Any],
        rom: int | Callable[..., Any],
        subnet: IPv4Network,
        architecture: str = Constants.X86,
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
        super().__init__(
            ipc,
            frequency,
            num_cores,
            cpu_tdps,
            cpu_mode,
            ram,
            rom,
            architecture,
            label,
            create_at,
            terminate_at,
            precursor,
        )
        self._subnet = subnet
        self._available_ip_addresses = list(subnet.hosts())

    @property
    def subnet(self) -> IPv4Network:
        """Returns the subnet of the vSwitch"""
        return self._subnet

    @property
    def available_ip_addresses(self) -> list[IPv4Address]:
        """Returns a list of available IP addresses in the subnet."""
        return self._available_ip_addresses
