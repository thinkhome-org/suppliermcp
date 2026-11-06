# Live supplier API inventory

## V2 operation reference

- [eD PUBLIC](ed_public-reference.md) and [eD PRIVATE](ed_private-reference.md)
- [100MEGA exports](mega-reference.md), [order service](mega_order-reference.md) and [default service](mega_default-reference.md)
- [Calling reads](operation-reads.md) and [candidate acceptance](v2-acceptance.md)

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

## Contract review on 2026-11-06

The two supplier emails and two saved text extracts identified the eD documentation and the 100MEGA export and order services. Their account details, examples, and attachments stay outside the repository. Comparing the two supplied eD PDFs with the current WSDLs found 19 PUBLIC operations and 32 PRIVATE operations. The PUBLIC PDF describes 17. Both additional WSDL methods marked internal and the e-shop credential method are blocked. PRIVATE section 3.18 explicitly marks its transform method unimplemented. The other four PRIVATE exclusions create orders or change documents.

The authenticated 100MEGA export index still has 65 families, 120 export names and three mode columns. Each name and each weekday and hour matched the saved account inventory. The runtime inventory includes disabled modes. The three raw Default.asmx selectors are blocked because they accept arbitrary result types. A named export uses the corresponding fixed selector. The remaining Default.asmx method is a demonstration. Order.asmx advertises 29 methods. Its WSDL documents 15 reads returning order status, company or delivery-address data. Thirteen operations change state and ExecuteTrgX runs arbitrary named functionality. All 15 reads require document scope. Source metadata was fetched without invoking any order method. [100MEGA Order WSDL](https://i6ws.100mega.cz/Order.asmx?WSDL) and [order guide](https://i6ws.100mega.cz/OrderReadMe.txt).

The packaged decisions in [operation_contracts.json](../../src/suppliermcp/suppliers/operation_contracts.json) pin reviewed names, schemas and windows. Each SOAP entry records effect, scope, caller fields, result type and effect evidence. Each export records scope, evidence and indexes into the full, targeted and delta windows (ISO weekdays and Europe/Prague hours). Document-transfer acknowledgement semantics, order-token contents and shop-settings fields still require supplier confirmation. These families are blocked. Runtime account permission and the account's current availability must also be checked for any enabled read. This review established advertised contracts. Authenticated execution of each read is tracked separately.
