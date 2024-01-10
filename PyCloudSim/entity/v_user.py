from __future__ import annotations
from typing import Callable, List, TYPE_CHECKING

from Akatosh import Entity

if TYPE_CHECKING:
    from .v_gateway import vGateway


class vUser(Entity):
    def __init__(
        self,
        gateway: vGateway,
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
        super().__init__(label, create_at, terminate_at, precursor)

        self._host = gateway

    @property
    def host(self) -> vGateway:
        return self._host
    
