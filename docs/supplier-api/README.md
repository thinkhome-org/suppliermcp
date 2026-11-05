# Live supplier API inventory

Observed 2026-11-05. These are discovery results, not a declaration of working ingestion.

The JSON inventories contain all advertised operation names and product schema definitions. Business-document data was not requested. No account credentials or account-bearing download URLs are included.

## Initial 100MEGA reconnaissance

| Export family / variants | Scope | Data evidence |
|---|---|---|
| `AttCpsSti`, `AttCpsSti_El` | product_read_candidate | not_tested |
| `AttSti`, `AttSti_El` | product_read_candidate | not_tested |
| `ComBank`, `ComBank_El` | excluded_by_v1 | not_tested |
| `ComShipTo`, `ComShipTo_El` | excluded_by_v1 | not_tested |
| `Config`, `Config_El` | product_read_candidate | not_tested |
| `CpsSti` | product_read_candidate | not_tested |
| `CpsStiVal`, `CpsStiVal_El` | product_read_candidate | targeted_read_one_sku |
| `DocTrDel` | excluded_by_v1 | not_tested |
| `DocTrExp`, `DocTrExp_El` | excluded_by_v1 | not_tested |
| `DocTrInv` | excluded_by_v1 | not_tested |
| `DocTrLoa` | excluded_by_v1 | not_tested |
| `Order` | excluded_by_v1 | not_tested |
| `OrderDelivMode`, `OrderDelivMode_El` | excluded_by_v1 | not_tested |
| `OrderPaymentMode`, `OrderPaymentMode_El` | excluded_by_v1 | not_tested |
| `OrderQueue`, `OrderQueue_El` | excluded_by_v1 | not_tested |
| `OrderToken`, `OrderToken_El` | excluded_by_v1 | not_tested |
| `Queue`, `Queue_El` | product_read_candidate | not_tested |
| `Reclaim` | excluded_by_v1 | not_tested |
| `SCategorySys`, `SCategorySys_El` | product_read_candidate | not_tested |
| `Service` | excluded_by_v1 | not_tested |
| `SPresentTree`, `SPresentTree_El` | product_read_candidate | not_tested |
| `SPresentTreeType`, `SPresentTreeType_El` | product_read_candidate | not_tested |
| `StiPacking`, `StiPacking_El` | product_read_candidate | targeted_read_one_sku |
| `StiRelation`, `StiRelation_El` | product_read_candidate | targeted_read_one_sku |
| `StiRelationCO`, `StiRelationCO_El` | product_read_candidate | not_tested |
| `StoItemActive`, `StoItemActive_El` | product_read_candidate | not_tested |
| `StoItemBase`, `StoItemBase_El` | product_read_candidate | not_tested |
| `StoItemEAN`, `StoItemEAN_El` | product_read_candidate | targeted_read_one_sku |
| `StoItemEPREL`, `StoItemEPREL_El` | product_read_candidate | not_tested |
| `StoItemGPSR` | product_read_candidate | not_tested |
| `StoItemHook`, `StoItemHook_El` | product_read_candidate | not_tested |
| `StoItemList`, `StoItemList_El` | product_read_candidate | not_tested |
| `StoItemNode`, `StoItemNode_El` | product_read_candidate | not_tested |
| `StoItemPriceEU`, `StoItemPriceEU_El` | product_read_candidate | not_tested |
| `StoItemPriceOrd`, `StoItemPriceOrd_El` | product_read_candidate | targeted_read_one_sku |
| `StoItemPriceOrdCur`, `StoItemPriceOrdCur_El` | product_read_candidate | targeted_read_one_sku |
| `StoItemQtyFree`, `StoItemQtyFree_El` | product_read_candidate | full_read_33431_rows |
| `StoItemQtyFreeBO`, `StoItemQtyFreeBO_El` | product_read_candidate | not_tested |
| `StoItemQtyFreeEx`, `StoItemQtyFreeEx_El` | product_read_candidate | not_tested |
| `StoItemQtyFreeExQud`, `StoItemQtyFreeExQud_El` | product_read_candidate | not_tested |
| `StoItemQtyFreeExQudT`, `StoItemQtyFreeExQudT_El` | product_read_candidate | not_tested |
| `StoItemShop_El` | product_read_candidate | not_tested |
| `StoItemShoptet_El` | product_read_candidate | not_tested |
| `StoItemSiv`, `StoItemSiv_El` | product_read_candidate | not_tested |
| `StrStiSync`, `StrStiSync_El` | product_read_candidate | not_tested |
| `X-100M`, `X-100M_El` | product_read_candidate | not_tested |
| `X-ASM-CpsStiVal`, `X-ASM-CpsStiVal_El` | product_read_candidate | not_tested |
| `X-ASM-StiRelation`, `X-ASM-StiRelation_El` | product_read_candidate | not_tested |
| `X-ASM-StoItemSiv`, `X-ASM-StoItemSiv_El` | product_read_candidate | not_tested |
| `X-CpsStiVal`, `X-CpsStiVal_El` | product_read_candidate | not_tested |
| `X-Cybex`, `X-Cybex_El` | product_read_candidate | not_tested |
| `X-EAN`, `X-EAN_El` | product_read_candidate | not_tested |
| `X-EnterpriceB2C`, `X-EnterpriceB2C_El` | product_read_candidate | not_tested |
| `X-HalshopDayOffer`, `X-HalshopDayOffer_El` | product_read_candidate | not_tested |
| `X-HOG`, `X-HOG_El` | product_read_candidate | not_tested |
| `X-LMStiPacking`, `X-LMStiPacking_El` | product_read_candidate | not_tested |
| `X-Retail`, `X-Retail_El` | product_read_candidate | not_tested |
| `X-StoItemClass`, `X-StoItemClass_El` | product_read_candidate | not_tested |
| `X-StoItemPack`, `X-StoItemPack_El` | product_read_candidate | not_tested |
| `X-StoItemPriceEU`, `X-StoItemPriceEU_El` | product_read_candidate | not_tested |
| `X-StoItemPriceOrdCur`, `X-StoItemPriceOrdCur_El` | product_read_candidate | not_tested |
| `X-StoItemVariant`, `X-StoItemVariant_El` | product_read_candidate | not_tested |
| `X-StoItemWoutNote`, `X-StoItemWoutNote_El` | product_read_candidate | not_tested |
| `ZCompany`, `ZCompany_El` | excluded_by_v1 | not_tested |
| `ZShop`, `ZShop_El` | excluded_by_v1 | not_tested |

94 product-related schema requests: 89 actual schemas; SPresentTree and X-HOG variants returned HTTP 500; StoItemShop_El_Schema returned an empty Result. An empty targeted relationship result does not prove nonempty relationship semantics.

## Initial eD reconnaissance (before adapter fixes)

PUBLIC export status succeeded through the existing Codex connector and directly through the repository gateway. The response uses lowercase `url`, `fileName`, `isReady`; initial adapter parsing failed to follow that URL. The XML file was downloaded separately for read-only diagnosis (619,833,546 bytes). The initial record parser read all 124,532 products and offers in 26.26 seconds; database publication and MCP queries remain untested. Initial 100MEGA parsing read 33,431 stock records, but both tested price variants produced no normalized price/currency. PRIVATE WSDL is reachable, but PRIVATE account calls were not made.

Sources: [100MEGA capability page](https://i6ws.100mega.cz/ResultTypeInfo.ashx), [100MEGA documentation](https://i6ws.100mega.cz/WebServiceInfoMail.txt), [eD PUBLIC WSDL](https://public-ws-cz.elinkx.biz/service.asmx?WSDL), [eD PRIVATE WSDL](https://private-ws-cz.elinkx.biz/service.asmx?WSDL).

See the live activation design in `../superpowers/specs/2026-11-05-live-supplier-data-design.md` for the proposed implementation and acceptance criteria.

## Live adapter follow-up

The repaired eD adapter downloaded the documented ZIP (47,069,717 bytes), parsed all 124,532 products/offers, and used 61,374,464 bytes peak RSS in the measured run. An XML replay used 36,077,568 bytes peak RSS. The 100MEGA product-only probe obeyed each advertised mode window; 81 captured responses replay successfully through the revised parser. Empty responses, restricted windows and methods requiring tree IDs are listed separately in the JSON inventory. Some special exports ignore the supplied SKU and return many rows; no targeted completeness is inferred. Subsequent database publication and MCP acceptance are recorded in [validation evidence](../validation.md); parser replay alone is not database acceptance.

## Current evidence format

Use each JSON inventory for current endpoint-level results. The initial family table above is historical; `endpoint_validation`, `live_probes`, and `capture_parser_replay` distinguish actual calls, empty responses, parser validation, and database acceptance. Equivalent representations are not all polled on a schedule. Advertised windows now use the corrected enabled-cell parser; a disabled method does not inherit the hours printed in its disabled table cell.

## Night-window acceptance

Full baseline, price and parameter exports were published; the final checked catalog/index both contained 157,959 active products at revision 19. See [live validation](../validation.md) for measured timings, actual MCP/Codex checks and remaining queued enrichments. `published_full_export` records a full-mode import; only `verified_complete: true` asserts the separately verified completeness contract. A queued or parser-replayed export is not a completed integration test.
