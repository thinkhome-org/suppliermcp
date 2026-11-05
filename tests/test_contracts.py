from decimal import Decimal
from itertools import product

import pytest
from pydantic import ValidationError

from suppliermcp.catalog.contracts import Identifier, Offer, QuantityRequest
from suppliermcp.config import Settings


@pytest.mark.parametrize("enabled", list(product([False, True], repeat=3)))
def test_optional_sources(enabled, monkeypatch):
    names = ["ED_PUBLIC", "ED_PRIVATE", "MEGA"]
    for name, active in zip(names, enabled, strict=True):
        for key in ["LOGIN", "PASSWORD"]:
            monkeypatch.delenv(f"SUPPLIERMCP_{name}_{key}", raising=False)
            if active:
                monkeypatch.setenv(f"SUPPLIERMCP_{name}_{key}", "supplier-password")
    settings = Settings.from_env()
    assert settings.enabled_interfaces == [
        n.lower() for n, e in zip(names, enabled, strict=True) if e
    ]
    assert "supplier-password" not in repr(settings)
    assert "supplier-password" not in settings.model_dump_json()


def test_partial_credentials_rejected(monkeypatch):
    monkeypatch.setenv("SUPPLIERMCP_MEGA_LOGIN", "account")
    monkeypatch.delenv("SUPPLIERMCP_MEGA_PASSWORD", raising=False)
    with pytest.raises(ValueError, match="both"):
        Settings.from_env()


def test_identity_and_money():
    assert Identifier(kind="sku", supplier="mega", value="00123").value == "00123"
    assert Offer(item_id="mega:1", unit_net="0.10").model_dump(mode="json")["unit_net"] == "0.10"
    for value in ["NaN", "Infinity", "-1"]:
        with pytest.raises(ValidationError):
            Offer(item_id="mega:1", unit_net=value)
    for qty in ["0", "-1", "NaN"]:
        with pytest.raises(ValidationError):
            QuantityRequest(quantity=qty)
    assert QuantityRequest().quantity == Decimal(1)
    with pytest.raises(ValidationError):
        Identifier(kind="mpn", value="ABC")
    with pytest.raises(ValidationError):
        Identifier(kind="sku", supplier="mega", value="001", unexpected=True)


def test_resource_limits_must_be_positive():
    with pytest.raises(ValidationError):
        Settings(max_download_bytes=0)
    with pytest.raises(ValidationError):
        Settings(page_size=101)
