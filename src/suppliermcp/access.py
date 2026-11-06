"""Authorization shared by the Python, HTTP and MCP interfaces."""

import json
from dataclasses import dataclass
from typing import Literal

from suppliermcp.catalog.contracts import CatalogError

Scope = Literal["catalog:read", "documents:read"]


@dataclass(frozen=True)
class Identity:
    issuer: str
    subject: str
    client_id: str | None
    scopes: frozenset[str]

    @property
    def principal(self) -> str:
        return json.dumps([self.issuer, self.subject, self.client_id], separators=(",", ":"))


class AccessDenied(CatalogError):
    def __init__(self, status_code: Literal[401, 403]):
        self.status_code = status_code
        super().__init__("unauthorized" if status_code == 401 else "forbidden")


def require_scope(identity: Identity, scope: Scope) -> None:
    if scope not in identity.scopes:
        raise AccessDenied(403)
