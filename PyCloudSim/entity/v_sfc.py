from __future__ import annotations

from typing import TYPE_CHECKING, Callable, List, Tuple, Union

from Akatosh import Entity, EntityList

from PyCloudSim import logger, simulation
from PyCloudSim.entity.v_apicall import vAPICall

from .v_container import vContainer
from .v_packet import vPacket
from .v_process import vContainerProcess
from .v_sofware_entity import vSoftwareEntity
from .v_user import vUser

if TYPE_CHECKING:
    from .v_container import vContainer
    from .v_user import vUser


class vSFC(vSoftwareEntity):
    def __init__(
        self,
        api_calls: List[Tuple[Union[vContainer, vUser], Union[vContainer, vUser], str]],
        label: str | None = None,
        create_at: int
        | float
        | Callable[..., int]
        | Callable[..., float]
        | None = None,
        precursor: Entity | List[Entity] | None = None,
    ) -> None:
        super().__init__(label=label, create_at=create_at, precursor=precursor)

        self._api_calls: List[vAPICall] = EntityList()
        for call in api_calls:
            pass
