"""Field-level eD authority: placeholders are not observations of zero."""

from collections import defaultdict

BASELINE_METHODS = {"getProductCatalogueDownloadXML", "getProductCatalogueDownloadZIP"}
PLACEHOLDERS = {
    "YourPrice",
    "YourPriceWithFees",
    "GarbageFee",
    "AuthorFee",
    "ValuePack",
    "ValuePackQty",
    "DealerPrice",
    "EndUserPrice",
    "Vat",
    "OnStock",
}


def merge_ed(observations):
    groups = defaultdict(list)
    for o in observations:
        if o.state in {"known", "conflict"}:
            groups[o.field].append(o)
    result = []
    for values in groups.values():
        if len({str(o.value) for o in values}) == 1:
            result.append(max(values, key=lambda o: o.fetched_at))
        elif all(o.source_updated_at is not None for o in values):
            latest = max(o.source_updated_at for o in values)
            winners = [o for o in values if o.source_updated_at == latest]
            if len({str(o.value) for o in winners}) == 1:
                result.append(winners[0])
            else:
                result.extend(o.model_copy(update={"state": "conflict"}) for o in winners)
        else:
            result.extend(o.model_copy(update={"state": "conflict"}) for o in values)
    return result
