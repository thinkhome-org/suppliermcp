"""Reviewed wire bindings and account slots. Only code can register a service."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal


@dataclass(frozen=True)
class ServiceProfile:
    supplier: str
    family: Literal["elinkx", "i6ws"]
    account: str
    host: str
    path: str
    binding: Literal["wrapped", "bare", "export"]
    empty_body: bool = False

    @property
    def url(self):
        return f"https://{self.host}{self.path}"


# Interfaces with a reviewed catalog adapter. Other services support direct reads only.
CATALOG_INTERFACES = ("ed_public", "ed_private", "mega")

_MEGA_HOST = "i6ws.100mega.cz"
SERVICES = MappingProxyType(
    {
        "ed_public": ServiceProfile(
            "ed", "elinkx", "ed_public", "public-ws-cz.elinkx.biz", "/service.asmx", "wrapped"
        ),
        "ed_private": ServiceProfile(
            "ed", "elinkx", "ed_private", "private-ws-cz.elinkx.biz", "/service.asmx", "wrapped"
        ),
        "mega": ServiceProfile("mega", "i6ws", "mega", _MEGA_HOST, "/Default.asmx", "export"),
        "mega_order": ServiceProfile(
            "mega", "i6ws", "mega", _MEGA_HOST, "/Order.asmx", "bare", empty_body=True
        ),
        "mega_default": ServiceProfile("mega", "i6ws", "mega", _MEGA_HOST, "/Default.asmx", "bare"),
    }
)
