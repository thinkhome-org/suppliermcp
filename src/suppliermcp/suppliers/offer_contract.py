"""Normalize only account-verified commercial semantics; absent contracts stay unknown."""

from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import ValidationError

from suppliermcp.catalog.contracts import CatalogError, Observation, Offer


def apply_contract(offer, values, contract, manifest):
    updates = {}
    for field in ["order_multiple", "fees_net", "currency"]:
        native = contract.get(field + "_field")
        value = values.get(native) if native else contract.get(field)
        if value is not None and getattr(offer, field) is None:
            updates[field] = value
    field = contract.get("timestamp_field") or contract.get("export_timestamp_field")
    if field and contract.get("timestamp_is_price_evidence") is True and values.get(field):
        try:
            timestamp = datetime.fromisoformat(values[field].replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                timezone = contract.get("timezone")
                if not timezone:
                    raise ValueError()
                timestamp = timestamp.replace(tzinfo=ZoneInfo(timezone))
            updates["source_updated_at"] = timestamp
            updates["freshness_seconds"] = contract.get("freshness_seconds")
        except (ValueError, KeyError):
            raise CatalogError("invalid_source_timestamp") from None
    try:
        result = Offer.model_validate(offer.model_dump() | updates)
    except ValidationError:
        raise CatalogError("invalid_offer_contract") from None
    for field, value in updates.items():
        result.observations.append(
            Observation(
                interface=manifest.interface,
                endpoint=manifest.endpoint,
                field=field,
                value=str(value),
                derivation="mapped",
                artifact_sha256=manifest.artifact_sha256,
                fetched_at=manifest.started_at,
                source_updated_at=result.source_updated_at,
            )
        )
    return result
