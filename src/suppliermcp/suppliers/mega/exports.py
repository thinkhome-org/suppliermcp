"""Product-only export vocabulary verified from the supplier capability/schema pages."""

import hashlib
from xml.etree.ElementTree import tostring

from suppliermcp.catalog.contracts import Observation, SchemaRecord

PRODUCT_EXPORTS = frozenset(
    [
        "AttCpsSti",
        "AttCpsSti_El",
        "AttSti",
        "AttSti_El",
        "Config",
        "Config_El",
        "CpsSti",
        "CpsStiVal",
        "CpsStiVal_El",
        "Queue",
        "Queue_El",
        "SCategorySys",
        "SCategorySys_El",
        "SPresentTree",
        "SPresentTreeType",
        "SPresentTreeType_El",
        "SPresentTree_El",
        "StiPacking",
        "StiPacking_El",
        "StiRelation",
        "StiRelationCO",
        "StiRelationCO_El",
        "StiRelation_El",
        "StoItemActive",
        "StoItemActive_El",
        "StoItemBase",
        "StoItemBase_El",
        "StoItemEAN",
        "StoItemEAN_El",
        "StoItemEPREL",
        "StoItemEPREL_El",
        "StoItemGPSR",
        "StoItemHook",
        "StoItemHook_El",
        "StoItemList",
        "StoItemList_El",
        "StoItemNode",
        "StoItemNode_El",
        "StoItemPriceEU",
        "StoItemPriceEU_El",
        "StoItemPriceOrd",
        "StoItemPriceOrdCur",
        "StoItemPriceOrdCur_El",
        "StoItemPriceOrd_El",
        "StoItemQtyFree",
        "StoItemQtyFreeBO",
        "StoItemQtyFreeBO_El",
        "StoItemQtyFreeEx",
        "StoItemQtyFreeExQud",
        "StoItemQtyFreeExQudT",
        "StoItemQtyFreeExQudT_El",
        "StoItemQtyFreeExQud_El",
        "StoItemQtyFreeEx_El",
        "StoItemQtyFree_El",
        "StoItemShop_El",
        "StoItemShoptet_El",
        "StoItemSiv",
        "StoItemSiv_El",
        "StrStiSync",
        "StrStiSync_El",
        "X-100M",
        "X-100M_El",
        "X-ASM-CpsStiVal",
        "X-ASM-CpsStiVal_El",
        "X-ASM-StiRelation",
        "X-ASM-StiRelation_El",
        "X-ASM-StoItemSiv",
        "X-ASM-StoItemSiv_El",
        "X-CpsStiVal",
        "X-CpsStiVal_El",
        "X-Cybex",
        "X-Cybex_El",
        "X-EAN",
        "X-EAN_El",
        "X-EnterpriceB2C",
        "X-EnterpriceB2C_El",
        "X-HOG",
        "X-HOG_El",
        "X-HalshopDayOffer",
        "X-HalshopDayOffer_El",
        "X-LMStiPacking",
        "X-LMStiPacking_El",
        "X-Retail",
        "X-Retail_El",
        "X-StoItemClass",
        "X-StoItemClass_El",
        "X-StoItemPack",
        "X-StoItemPack_El",
        "X-StoItemPriceEU",
        "X-StoItemPriceEU_El",
        "X-StoItemPriceOrdCur",
        "X-StoItemPriceOrdCur_El",
        "X-StoItemVariant",
        "X-StoItemVariant_El",
        "X-StoItemWoutNote",
        "X-StoItemWoutNote_El",
    ]
)


def values(element):
    return dict(element.attrib) | {
        c.tag.rsplit("}", 1)[-1]: c.text or "" for c in element if not len(c) and not c.attrib
    }


def facts(manifest, data, prefix="", key="", many=False):
    return [
        Observation(
            interface="mega",
            endpoint=manifest.endpoint,
            field=prefix + k,
            value=v,
            value_key=key,
            cardinality="many" if many else "one",
            fetched_at=manifest.started_at,
            artifact_sha256=manifest.artifact_sha256,
        )
        for k, v in data.items()
    ]


def nested_facts(manifest, element, prefix=""):
    result = []
    for child in element:
        if not child.attrib and not len(child):
            continue
        name = prefix + child.tag.rsplit("}", 1)[-1]
        key = hashlib.sha256(tostring(child)).hexdigest()
        result.extend(facts(manifest, values(child), name + ".", key, True))
        result.extend(nested_facts(manifest, child, name + "."))
    return result


def normalize_record(manifest, element, root_values=None):
    data = values(element)
    tag = element.tag.rsplit("}", 1)[-1]
    if not data:
        return []
    result = []
    root_facts = facts(manifest, root_values or {}, prefix="root:")
    if tag in {"StoItem", "SHOPITEM"}:
        reference = (
            {"item_id": "mega:" + (data.get("Id") or data["id"])}
            if data.get("Id") or data.get("id")
            else {
                "sku": data.get("Code") or data.get("Kod") or data.get("CODE"),
                "supplier": "mega",
            }
        )
        if not reference.get("item_id") and not reference.get("sku"):
            from suppliermcp.catalog.contracts import CatalogError

            raise CatalogError("missing_product_identity")
        key = hashlib.sha256(tostring(element)).hexdigest()
        observations = (
            root_facts + facts(manifest, data, key=key, many=True) + nested_facts(manifest, element)
        )
        result.append(
            SchemaRecord(
                interface="mega",
                kind="product_facts",
                values={
                    **reference,
                    "observations": [o.model_dump(mode="json") for o in observations],
                },
            )
        )
    elif data.get("StiId"):
        item_id = "mega:" + data["StiId"]
        key = data.get("Id") or hashlib.sha256(tostring(element)).hexdigest()
        observations = (
            root_facts
            + facts(manifest, data, tag + ".", key, True)
            + nested_facts(manifest, element, tag + ".")
        )
        if data.get("CpaId") and "Value" in data:
            if data.get("Name"):
                result.append(
                    SchemaRecord(
                        interface="mega",
                        kind="parameter",
                        values={
                            "code": data["CpaId"],
                            "label": data["Name"],
                            "cardinality": "one" if data.get("Single") == "1" else "many",
                        },
                    )
                )
            observations.extend(
                facts(
                    manifest,
                    {"parameter:" + data["CpaId"]: data["Value"]},
                    key=key,
                    many=data.get("Single") != "1",
                )
            )
        if data.get("CpaId") and data.get("Measure"):
            # CpsStiVal schema declares Measure fixed.14.4; its unit is not declared.
            observations.append(
                Observation(
                    interface="mega",
                    endpoint=manifest.endpoint,
                    field="parameter:" + data["CpaId"] + ":measure",
                    value=data["Measure"],
                    value_type="number",
                    value_key=key,
                    cardinality="one" if data.get("Single") == "1" else "many",
                    fetched_at=manifest.started_at,
                    artifact_sha256=manifest.artifact_sha256,
                )
            )
        result.append(
            SchemaRecord(
                interface="mega",
                kind="product_facts",
                values={
                    "item_id": item_id,
                    "observations": [o.model_dump(mode="json") for o in observations],
                },
            )
        )
        if tag == "StiRelation" and data.get("StiIdR"):
            result.append(
                SchemaRecord(
                    interface="mega",
                    kind="relationship",
                    values={
                        "item_id": item_id,
                        "target_id": "mega:" + data["StiIdR"],
                        "kind": data.get("SreId", "unknown"),
                        "name": data.get("SreName"),
                        "interface": "mega",
                        "endpoint": manifest.endpoint,
                        "native": data,
                    },
                )
            )
    else:
        result.append(
            SchemaRecord(
                interface="mega",
                kind=manifest.endpoint,
                values={"record_type": tag, **data, "_xml": tostring(element, encoding="unicode")},
            )
        )
    return result
