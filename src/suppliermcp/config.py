"""Server-only configuration. Supplier interfaces may be independently absent."""

import os
from pathlib import Path

from pydantic import Field, SecretStr

from suppliermcp.catalog.contracts import Model


class Settings(Model):
    credentials: dict[str, tuple[SecretStr, SecretStr]] = Field(
        default_factory=dict, repr=False, exclude=True
    )
    database_url: SecretStr = Field(
        default=SecretStr("postgresql://localhost/suppliermcp"), repr=False, exclude=True
    )
    typesense_url: str = "http://typesense:8108"
    typesense_key: SecretStr = Field(default=SecretStr(""), repr=False, exclude=True)
    artifact_dir: Path = Path("artifacts")
    source_contracts_path: Path | None = None
    allowed_hosts: list[str] = Field(default_factory=lambda: ["127.0.0.1:*", "localhost:*"])
    allowed_origins: list[str] = Field(default_factory=list)
    auth_public_key: str = ""
    auth_issuer: str = "suppliermcp"
    auth_audience: str = "suppliermcp"
    max_download_bytes: int = Field(default=256 * 1024**2, gt=0)
    max_expanded_bytes: int = Field(default=1024**3, gt=0)
    artifact_budget: int = Field(default=5 * 1024**3, gt=0)
    max_description_bytes: int = Field(default=2 * 1024**2, gt=0)
    max_response_bytes: int = Field(default=256 * 1024, gt=0)
    page_size: int = Field(default=20, gt=0, le=100)
    result_ttl_seconds: int = Field(default=1800, gt=0)
    max_result_rows: int = Field(default=100_000, gt=0)

    @property
    def enabled_interfaces(self) -> list[str]:
        return list(self.credentials)

    @classmethod
    def from_env(cls):
        credentials = {}
        for interface in ["ed_public", "ed_private", "mega"]:
            prefix = f"SUPPLIERMCP_{interface.upper()}"
            login, password = os.getenv(prefix + "_LOGIN"), os.getenv(prefix + "_PASSWORD")
            if bool(login) != bool(password):
                raise ValueError(f"{interface} requires both login and password")
            if login and password:
                credentials[interface] = (SecretStr(login), SecretStr(password))
        values = {"credentials": credentials}
        for name in cls.model_fields:
            if name == "credentials":
                continue
            value = os.getenv("SUPPLIERMCP_" + name.upper())
            if value is not None:
                if name in {"allowed_hosts", "allowed_origins"}:
                    import json

                    value = json.loads(value)
                values[name] = value
        return cls(**values)
