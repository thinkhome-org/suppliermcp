# 100MEGA exports

Generated from the reviewed runtime registry. Use the exact operation ID with the Python, REST or MCP interface. An input ending in ? is optional in the supplier contract. The service may enforce stricter input rules for a safe read.

[Calling and paging](operation-reads.md) · [Live acceptance](v2-acceptance.md)

Hours use Europe/Prague. Weekdays use ISO numbering (Monday = 1). The installation's authenticated capability list must also permit the mode.

## mega.AttCpsSti.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `AttCpsSti_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Attachments of StoItem's parameters.

## mega.AttCpsSti.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `AttCpsSti_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Attachments of StoItem's parameters.

## mega.AttCpsSti.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `AttCpsSti_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Attachments of StoItem's parameters.

## mega.AttCpsSti_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `AttCpsSti_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Attachments of StoItem's parameters.

## mega.AttCpsSti_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `AttCpsSti_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Attachments of StoItem's parameters.

## mega.AttCpsSti_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `AttCpsSti_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Attachments of StoItem's parameters.

## mega.AttSti.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `AttSti_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Export Attachments of StoItems.

## mega.AttSti.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `AttSti_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Export Attachments of StoItems.

## mega.AttSti.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `AttSti_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Attachments of StoItems.

## mega.AttSti_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `AttSti_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Export Attachments of StoItems.

## mega.AttSti_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `AttSti_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Export Attachments of StoItems.

## mega.AttSti_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `AttSti_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Attachments of StoItems.

## mega.ComBank.delta

- Excluded from client calls (`blocked`).
- Evidence: List of client's bank accounts.

## mega.ComBank.full

- Scope: `documents:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ComBank_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: List of client's bank accounts.

## mega.ComBank.targeted

- Excluded from client calls (`blocked`).
- Evidence: List of client's bank accounts.

## mega.ComBank_El.delta

- Excluded from client calls (`blocked`).
- Evidence: List of client's bank accounts.

## mega.ComBank_El.full

- Scope: `documents:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ComBank_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: List of client's bank accounts.

## mega.ComBank_El.targeted

- Excluded from client calls (`blocked`).
- Evidence: List of client's bank accounts.

## mega.ComShipTo.delta

- Excluded from client calls (`blocked`).
- Evidence: List of ShipTo address.

## mega.ComShipTo.full

- Scope: `documents:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ComShipTo_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: List of ShipTo address.

## mega.ComShipTo.targeted

- Excluded from client calls (`blocked`).
- Evidence: List of ShipTo address.

## mega.ComShipTo_El.delta

- Excluded from client calls (`blocked`).
- Evidence: List of ShipTo address.

## mega.ComShipTo_El.full

- Scope: `documents:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ComShipTo_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: List of ShipTo address.

## mega.ComShipTo_El.targeted

- Excluded from client calls (`blocked`).
- Evidence: List of ShipTo address.

## mega.Config.delta

- Excluded from client calls (`blocked`).
- Evidence: Configurator data.

## mega.Config.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `Config_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Configurator data.

## mega.Config.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `Config_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Configurator data.

## mega.Config_El.delta

- Excluded from client calls (`blocked`).
- Evidence: Configurator data.

## mega.Config_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `Config_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Configurator data.

## mega.Config_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `Config_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Configurator data.

## mega.CpsSti.delta

- Excluded from client calls (`blocked`).
- Evidence: Export parameters of StoItems include parameter's definition.

## mega.CpsSti.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `CpsSti_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Export parameters of StoItems include parameter's definition.

## mega.CpsSti.targeted

- Excluded from client calls (`blocked`).
- Evidence: Export parameters of StoItems include parameter's definition.

## mega.CpsStiVal.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `CpsStiVal_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export parameters of StoItems - Name x Value only (filtered by Code of StoItem).

## mega.CpsStiVal.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `CpsStiVal_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Export parameters of StoItems - Name x Value only (filtered by Code of StoItem).

## mega.CpsStiVal.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `CpsStiVal_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export parameters of StoItems - Name x Value only (filtered by Code of StoItem).

## mega.CpsStiVal_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `CpsStiVal_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export parameters of StoItems - Name x Value only (filtered by Code of StoItem).

## mega.CpsStiVal_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `CpsStiVal_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Export parameters of StoItems - Name x Value only (filtered by Code of StoItem).

## mega.CpsStiVal_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `CpsStiVal_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export parameters of StoItems - Name x Value only (filtered by Code of StoItem).

## mega.DocTrDel.delta

- Excluded from client calls (`blocked`).
- Evidence: Document Transfer - Delivery. Transfer acknowledgement effects are unverified.

## mega.DocTrDel.full

- Excluded from client calls (`blocked`).
- Evidence: Document Transfer - Delivery. Transfer acknowledgement effects are unverified.

## mega.DocTrDel.targeted

- Excluded from client calls (`blocked`).
- Evidence: Document Transfer - Delivery. Transfer acknowledgement effects are unverified.

## mega.DocTrExp.delta

- Excluded from client calls (`blocked`).
- Evidence: Document Transfer - Expedition (Format for import into I6). Transfer acknowledgement effects are unverified.

## mega.DocTrExp.full

- Excluded from client calls (`blocked`).
- Evidence: Document Transfer - Expedition (Format for import into I6). Transfer acknowledgement effects are unverified.

## mega.DocTrExp.targeted

- Excluded from client calls (`blocked`).
- Evidence: Document Transfer - Expedition (Format for import into I6). Transfer acknowledgement effects are unverified.

## mega.DocTrExp_El.delta

- Excluded from client calls (`blocked`).
- Evidence: Document Transfer - Expedition (Format for import into I6). Transfer acknowledgement effects are unverified.

## mega.DocTrExp_El.full

- Excluded from client calls (`blocked`).
- Evidence: Document Transfer - Expedition (Format for import into I6). Transfer acknowledgement effects are unverified.

## mega.DocTrExp_El.targeted

- Excluded from client calls (`blocked`).
- Evidence: Document Transfer - Expedition (Format for import into I6). Transfer acknowledgement effects are unverified.

## mega.DocTrInv.delta

- Excluded from client calls (`blocked`).
- Evidence: Document Transfer - Invoice (Format for import into I6). Transfer acknowledgement effects are unverified.

## mega.DocTrInv.full

- Excluded from client calls (`blocked`).
- Evidence: Document Transfer - Invoice (Format for import into I6). Transfer acknowledgement effects are unverified.

## mega.DocTrInv.targeted

- Excluded from client calls (`blocked`).
- Evidence: Document Transfer - Invoice (Format for import into I6). Transfer acknowledgement effects are unverified.

## mega.DocTrLoa.delta

- Excluded from client calls (`blocked`).
- Evidence: Document Transfer - Loan. Transfer acknowledgement effects are unverified.

## mega.DocTrLoa.full

- Excluded from client calls (`blocked`).
- Evidence: Document Transfer - Loan. Transfer acknowledgement effects are unverified.

## mega.DocTrLoa.targeted

- Excluded from client calls (`blocked`).
- Evidence: Document Transfer - Loan. Transfer acknowledgement effects are unverified.

## mega.Order.delta

- Scope: `documents:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `Order_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of Orders with Items include ShipTo and B2C informations. If is use method without parameters, are returned all open orders.

## mega.Order.full

- Scope: `documents:read`
- Supplier inputs: none beyond server-side authentication
- Output: `Order_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of Orders with Items include ShipTo and B2C informations. If is use method without parameters, are returned all open orders.

## mega.Order.targeted

- Scope: `documents:read`
- Supplier inputs: `code: string`
- Output: `Order_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of Orders with Items include ShipTo and B2C informations. If is use method without parameters, are returned all open orders.

## mega.OrderDelivMode.delta

- Excluded from client calls (`blocked`).
- Evidence: List of Delivery Mode for Order.asmx/Create method. Search ByCode: XX - find OrderDelivMode.Code = XX; {DemToPlace.CouCode}XX find OrderDelivMode with DemToPlace.CouCode = XXX; {DemToPlace_Disable} export only OrderDelivMode (without DemToPlace)

## mega.OrderDelivMode.full

- Scope: `documents:read`
- Supplier inputs: none beyond server-side authentication
- Output: `OrderDelivMode_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: List of Delivery Mode for Order.asmx/Create method. Search ByCode: XX - find OrderDelivMode.Code = XX; {DemToPlace.CouCode}XX find OrderDelivMode with DemToPlace.CouCode = XXX; {DemToPlace_Disable} export only OrderDelivMode (without DemToPlace)

## mega.OrderDelivMode.targeted

- Scope: `documents:read`
- Supplier inputs: `code: string`
- Output: `OrderDelivMode_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: List of Delivery Mode for Order.asmx/Create method. Search ByCode: XX - find OrderDelivMode.Code = XX; {DemToPlace.CouCode}XX find OrderDelivMode with DemToPlace.CouCode = XXX; {DemToPlace_Disable} export only OrderDelivMode (without DemToPlace)

## mega.OrderDelivMode_El.delta

- Excluded from client calls (`blocked`).
- Evidence: List of Delivery Mode for Order.asmx/Create method. Search ByCode: XX - find OrderDelivMode.Code = XX; {DemToPlace.CouCode}XX find OrderDelivMode with DemToPlace.CouCode = XXX; {DemToPlace_Disable} export only OrderDelivMode (without DemToPlace)

## mega.OrderDelivMode_El.full

- Scope: `documents:read`
- Supplier inputs: none beyond server-side authentication
- Output: `OrderDelivMode_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: List of Delivery Mode for Order.asmx/Create method. Search ByCode: XX - find OrderDelivMode.Code = XX; {DemToPlace.CouCode}XX find OrderDelivMode with DemToPlace.CouCode = XXX; {DemToPlace_Disable} export only OrderDelivMode (without DemToPlace)

## mega.OrderDelivMode_El.targeted

- Scope: `documents:read`
- Supplier inputs: `code: string`
- Output: `OrderDelivMode_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: List of Delivery Mode for Order.asmx/Create method. Search ByCode: XX - find OrderDelivMode.Code = XX; {DemToPlace.CouCode}XX find OrderDelivMode with DemToPlace.CouCode = XXX; {DemToPlace_Disable} export only OrderDelivMode (without DemToPlace)

## mega.OrderPaymentMode.delta

- Excluded from client calls (`blocked`).
- Evidence: List of Payment Mode for Order.asmx/Create method.

## mega.OrderPaymentMode.full

- Scope: `documents:read`
- Supplier inputs: none beyond server-side authentication
- Output: `OrderPaymentMode_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: List of Payment Mode for Order.asmx/Create method.

## mega.OrderPaymentMode.targeted

- Excluded from client calls (`blocked`).
- Evidence: List of Payment Mode for Order.asmx/Create method.

## mega.OrderPaymentMode_El.delta

- Excluded from client calls (`blocked`).
- Evidence: List of Payment Mode for Order.asmx/Create method.

## mega.OrderPaymentMode_El.full

- Scope: `documents:read`
- Supplier inputs: none beyond server-side authentication
- Output: `OrderPaymentMode_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: List of Payment Mode for Order.asmx/Create method.

## mega.OrderPaymentMode_El.targeted

- Excluded from client calls (`blocked`).
- Evidence: List of Payment Mode for Order.asmx/Create method.

## mega.OrderQueue.delta

- Excluded from client calls (`blocked`).
- Evidence: List of Queue for Order.asmx/Create/Order/@QudId method.

## mega.OrderQueue.full

- Scope: `documents:read`
- Supplier inputs: none beyond server-side authentication
- Output: `OrderQueue_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: List of Queue for Order.asmx/Create/Order/@QudId method.

## mega.OrderQueue.targeted

- Excluded from client calls (`blocked`).
- Evidence: List of Queue for Order.asmx/Create/Order/@QudId method.

## mega.OrderQueue_El.delta

- Excluded from client calls (`blocked`).
- Evidence: List of Queue for Order.asmx/Create/Order/@QudId method.

## mega.OrderQueue_El.full

- Scope: `documents:read`
- Supplier inputs: none beyond server-side authentication
- Output: `OrderQueue_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: List of Queue for Order.asmx/Create/Order/@QudId method.

## mega.OrderQueue_El.targeted

- Excluded from client calls (`blocked`).
- Evidence: List of Queue for Order.asmx/Create/Order/@QudId method.

## mega.OrderToken.delta

- Excluded from client calls (`blocked`).
- Evidence: List of info about Order Token(s). Token contents and reuse are unverified.

## mega.OrderToken.full

- Excluded from client calls (`blocked`).
- Evidence: List of info about Order Token(s). Token contents and reuse are unverified.

## mega.OrderToken.targeted

- Excluded from client calls (`blocked`).
- Evidence: List of info about Order Token(s). Token contents and reuse are unverified.

## mega.OrderToken_El.delta

- Excluded from client calls (`blocked`).
- Evidence: List of info about Order Token(s). Token contents and reuse are unverified.

## mega.OrderToken_El.full

- Excluded from client calls (`blocked`).
- Evidence: List of info about Order Token(s). Token contents and reuse are unverified.

## mega.OrderToken_El.targeted

- Excluded from client calls (`blocked`).
- Evidence: List of info about Order Token(s). Token contents and reuse are unverified.

## mega.Queue.delta

- Excluded from client calls (`blocked`).
- Evidence: Delivery term.

## mega.Queue.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `Queue_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Delivery term.

## mega.Queue.targeted

- Excluded from client calls (`blocked`).
- Evidence: Delivery term.

## mega.Queue_El.delta

- Excluded from client calls (`blocked`).
- Evidence: Delivery term.

## mega.Queue_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `Queue_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Delivery term.

## mega.Queue_El.targeted

- Excluded from client calls (`blocked`).
- Evidence: Delivery term.

## mega.Reclaim.delta

- Scope: `documents:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `Reclaim_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of Reclaim details.

## mega.Reclaim.full

- Scope: `documents:read`
- Supplier inputs: none beyond server-side authentication
- Output: `Reclaim_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of Reclaim details.

## mega.Reclaim.targeted

- Scope: `documents:read`
- Supplier inputs: `code: string`
- Output: `Reclaim_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of Reclaim details.

## mega.SCategorySys.delta

- Excluded from client calls (`blocked`).
- Evidence: Catalog of system categories.

## mega.SCategorySys.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `SCategorySys_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Catalog of system categories.

## mega.SCategorySys.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `SCategorySys_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Catalog of system categories.

## mega.SCategorySys_El.delta

- Excluded from client calls (`blocked`).
- Evidence: Catalog of system categories.

## mega.SCategorySys_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `SCategorySys_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Catalog of system categories.

## mega.SCategorySys_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `SCategorySys_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Catalog of system categories.

## mega.SPresentTree.delta

- Excluded from client calls (`blocked`).
- Evidence: Hiearchical presentation tree structure of stoitems. IdP... relation to parent tree (empty - top level); Sort... each level has reseved 3chars - Eg. AAA = first level, AAABBB = second level. ByCode method filter data by IdP.

## mega.SPresentTree.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `SPresentTree_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Hiearchical presentation tree structure of stoitems. IdP... relation to parent tree (empty - top level); Sort... each level has reseved 3chars - Eg. AAA = first level, AAABBB = second level. ByCode method filter data by IdP.

## mega.SPresentTree.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `SPresentTree_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Hiearchical presentation tree structure of stoitems. IdP... relation to parent tree (empty - top level); Sort... each level has reseved 3chars - Eg. AAA = first level, AAABBB = second level. ByCode method filter data by IdP.

## mega.SPresentTreeType.delta

- Excluded from client calls (`blocked`).
- Evidence: Type of SPresentTree (export complet tree type: resultType=SPresentTree&code=Id).

## mega.SPresentTreeType.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `SPresentTreeType_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Type of SPresentTree (export complet tree type: resultType=SPresentTree&code=Id).

## mega.SPresentTreeType.targeted

- Excluded from client calls (`blocked`).
- Evidence: Type of SPresentTree (export complet tree type: resultType=SPresentTree&code=Id).

## mega.SPresentTreeType_El.delta

- Excluded from client calls (`blocked`).
- Evidence: Type of SPresentTree (export complet tree type: resultType=SPresentTree&code=Id).

## mega.SPresentTreeType_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `SPresentTreeType_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Type of SPresentTree (export complet tree type: resultType=SPresentTree&code=Id).

## mega.SPresentTreeType_El.targeted

- Excluded from client calls (`blocked`).
- Evidence: Type of SPresentTree (export complet tree type: resultType=SPresentTree&code=Id).

## mega.SPresentTree_El.delta

- Excluded from client calls (`blocked`).
- Evidence: Hiearchical presentation tree structure of stoitems. IdP... relation to parent tree (empty - top level); Sort... each level has reseved 3chars - Eg. AAA = first level, AAABBB = second level. ByCode method filter data by IdP.

## mega.SPresentTree_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `SPresentTree_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Hiearchical presentation tree structure of stoitems. IdP... relation to parent tree (empty - top level); Sort... each level has reseved 3chars - Eg. AAA = first level, AAABBB = second level. ByCode method filter data by IdP.

## mega.SPresentTree_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `SPresentTree_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Hiearchical presentation tree structure of stoitems. IdP... relation to parent tree (empty - top level); Sort... each level has reseved 3chars - Eg. AAA = first level, AAABBB = second level. ByCode method filter data by IdP.

## mega.Service.delta

- Scope: `documents:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `Service_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of Service details.

## mega.Service.full

- Scope: `documents:read`
- Supplier inputs: none beyond server-side authentication
- Output: `Service_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of Service details.

## mega.Service.targeted

- Scope: `documents:read`
- Supplier inputs: `code: string`
- Output: `Service_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of Service details.

## mega.StiPacking.delta

- Excluded from client calls (`blocked`).
- Evidence: Export StoItem's Packing.

## mega.StiPacking.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StiPacking_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export StoItem's Packing.

## mega.StiPacking.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StiPacking_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export StoItem's Packing.

## mega.StiPacking_El.delta

- Excluded from client calls (`blocked`).
- Evidence: Export StoItem's Packing.

## mega.StiPacking_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StiPacking_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export StoItem's Packing.

## mega.StiPacking_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StiPacking_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export StoItem's Packing.

## mega.StiRelation.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `StiRelation_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Relations of StoItems.

## mega.StiRelation.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StiRelation_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Relations of StoItems.

## mega.StiRelation.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StiRelation_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Relations of StoItems.

## mega.StiRelationCO.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `StiRelationCO_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Relations-ConditionalOffer of StoItems.

## mega.StiRelationCO.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StiRelationCO_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Relations-ConditionalOffer of StoItems.

## mega.StiRelationCO.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StiRelationCO_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Relations-ConditionalOffer of StoItems.

## mega.StiRelationCO_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `StiRelationCO_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Relations-ConditionalOffer of StoItems.

## mega.StiRelationCO_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StiRelationCO_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Relations-ConditionalOffer of StoItems.

## mega.StiRelationCO_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StiRelationCO_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Relations-ConditionalOffer of StoItems.

## mega.StiRelation_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `StiRelation_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Relations of StoItems.

## mega.StiRelation_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StiRelation_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Relations of StoItems.

## mega.StiRelation_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StiRelation_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Relations of StoItems.

## mega.StoItemActive.delta

- Excluded from client calls (`blocked`).
- Evidence: List of active products.

## mega.StoItemActive.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemActive_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: List of active products.

## mega.StoItemActive.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemActive_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: List of active products.

## mega.StoItemActive_El.delta

- Excluded from client calls (`blocked`).
- Evidence: List of active products.

## mega.StoItemActive_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemActive_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: List of active products.

## mega.StoItemActive_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemActive_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: List of active products.

## mega.StoItemBase.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `StoItemBase_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Base informations about products.

## mega.StoItemBase.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemBase_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Base informations about products.

## mega.StoItemBase.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemBase_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 21, 22, 23.
- Evidence: Base informations about products.

## mega.StoItemBase_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `StoItemBase_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Base informations about products.

## mega.StoItemBase_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemBase_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Base informations about products.

## mega.StoItemBase_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemBase_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 21, 22, 23.
- Evidence: Base informations about products.

## mega.StoItemEAN.delta

- Excluded from client calls (`blocked`).
- Evidence: Export of StoItem EAN.

## mega.StoItemEAN.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemEAN_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of StoItem EAN.

## mega.StoItemEAN.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemEAN_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of StoItem EAN.

## mega.StoItemEAN_El.delta

- Excluded from client calls (`blocked`).
- Evidence: Export of StoItem EAN.

## mega.StoItemEAN_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemEAN_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of StoItem EAN.

## mega.StoItemEAN_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemEAN_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of StoItem EAN.

## mega.StoItemEPREL.delta

- Excluded from client calls (`blocked`).
- Evidence: Export of StoItem EPREL Info.

## mega.StoItemEPREL.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemEPREL_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of StoItem EPREL Info.

## mega.StoItemEPREL.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemEPREL_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of StoItem EPREL Info.

## mega.StoItemEPREL_El.delta

- Excluded from client calls (`blocked`).
- Evidence: Export of StoItem EPREL Info.

## mega.StoItemEPREL_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemEPREL_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of StoItem EPREL Info.

## mega.StoItemEPREL_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemEPREL_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of StoItem EPREL Info.

## mega.StoItemGPSR.delta

- Excluded from client calls (`blocked`).
- Evidence: Product's GPRS informations.

## mega.StoItemGPSR.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemGPSR_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Product's GPRS informations.

## mega.StoItemGPSR.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemGPSR_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Product's GPRS informations.

## mega.StoItemHook.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `StoItemHook_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Hooked products.

## mega.StoItemHook.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemHook_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Hooked products.

## mega.StoItemHook.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemHook_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Hooked products.

## mega.StoItemHook_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `StoItemHook_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Hooked products.

## mega.StoItemHook_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemHook_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Hooked products.

## mega.StoItemHook_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemHook_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Hooked products.

## mega.StoItemList.delta

- Excluded from client calls (`blocked`).
- Evidence: List of StoItems specified by Conditions in Code - Code can be: '{StrId}XXX' or '{ScaId}XXX or '{CpaId}XXX''

## mega.StoItemList.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemList_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: List of StoItems specified by Conditions in Code - Code can be: '{StrId}XXX' or '{ScaId}XXX or '{CpaId}XXX''

## mega.StoItemList.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemList_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: List of StoItems specified by Conditions in Code - Code can be: '{StrId}XXX' or '{ScaId}XXX or '{CpaId}XXX''

## mega.StoItemList_El.delta

- Excluded from client calls (`blocked`).
- Evidence: List of StoItems specified by Conditions in Code - Code can be: '{StrId}XXX' or '{ScaId}XXX or '{CpaId}XXX''

## mega.StoItemList_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemList_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: List of StoItems specified by Conditions in Code - Code can be: '{StrId}XXX' or '{ScaId}XXX or '{CpaId}XXX''

## mega.StoItemList_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemList_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: List of StoItems specified by Conditions in Code - Code can be: '{StrId}XXX' or '{ScaId}XXX or '{CpaId}XXX''

## mega.StoItemNode.delta

- Excluded from client calls (`blocked`).
- Evidence: Export references: StoItem - TreeNode.

## mega.StoItemNode.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemNode_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export references: StoItem - TreeNode.

## mega.StoItemNode.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemNode_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export references: StoItem - TreeNode.

## mega.StoItemNode_El.delta

- Excluded from client calls (`blocked`).
- Evidence: Export references: StoItem - TreeNode.

## mega.StoItemNode_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemNode_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export references: StoItem - TreeNode.

## mega.StoItemNode_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemNode_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export references: StoItem - TreeNode.

## mega.StoItemPriceEU.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `StoItemPriceEU_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of End User's prices.

## mega.StoItemPriceEU.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemPriceEU_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of End User's prices.

## mega.StoItemPriceEU.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemPriceEU_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of End User's prices.

## mega.StoItemPriceEU_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `StoItemPriceEU_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of End User's prices.

## mega.StoItemPriceEU_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemPriceEU_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of End User's prices.

## mega.StoItemPriceEU_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemPriceEU_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of End User's prices.

## mega.StoItemPriceOrd.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `StoItemPriceOrd_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Order prices. (Fix prices: PriceList, Price0-6 only on special permission.)

## mega.StoItemPriceOrd.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemPriceOrd_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Order prices. (Fix prices: PriceList, Price0-6 only on special permission.)

## mega.StoItemPriceOrd.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemPriceOrd_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Order prices. (Fix prices: PriceList, Price0-6 only on special permission.)

## mega.StoItemPriceOrdCur.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `StoItemPriceOrdCur_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Order prices in user's currency.

## mega.StoItemPriceOrdCur.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemPriceOrdCur_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Order prices in user's currency.

## mega.StoItemPriceOrdCur.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemPriceOrdCur_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Order prices in user's currency.

## mega.StoItemPriceOrdCur_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `StoItemPriceOrdCur_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Order prices in user's currency.

## mega.StoItemPriceOrdCur_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemPriceOrdCur_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Order prices in user's currency.

## mega.StoItemPriceOrdCur_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemPriceOrdCur_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Order prices in user's currency.

## mega.StoItemPriceOrd_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `StoItemPriceOrd_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Order prices. (Fix prices: PriceList, Price0-6 only on special permission.)

## mega.StoItemPriceOrd_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemPriceOrd_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Order prices. (Fix prices: PriceList, Price0-6 only on special permission.)

## mega.StoItemPriceOrd_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemPriceOrd_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Order prices. (Fix prices: PriceList, Price0-6 only on special permission.)

## mega.StoItemQtyFree.delta

- Excluded from client calls (`blocked`).
- Evidence: Products on store.

## mega.StoItemQtyFree.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemQtyFree_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Products on store.

## mega.StoItemQtyFree.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemQtyFree_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 22, 23.
- Evidence: Products on store.

## mega.StoItemQtyFreeBO.delta

- Excluded from client calls (`blocked`).
- Evidence: Products on store + blocked.

## mega.StoItemQtyFreeBO.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemQtyFreeBO_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Products on store + blocked.

## mega.StoItemQtyFreeBO.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemQtyFreeBO_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Products on store + blocked.

## mega.StoItemQtyFreeBO_El.delta

- Excluded from client calls (`blocked`).
- Evidence: Products on store + blocked.

## mega.StoItemQtyFreeBO_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemQtyFreeBO_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Products on store + blocked.

## mega.StoItemQtyFreeBO_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemQtyFreeBO_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Products on store + blocked.

## mega.StoItemQtyFreeEx.delta

- Excluded from client calls (`blocked`).
- Evidence: Products on store with availability and next ship.

## mega.StoItemQtyFreeEx.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemQtyFreeEx_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Products on store with availability and next ship.

## mega.StoItemQtyFreeEx.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemQtyFreeEx_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Products on store with availability and next ship.

## mega.StoItemQtyFreeExQud.delta

- Excluded from client calls (`blocked`).
- Evidence: Products on store with availability and next ship (itemized by QudId).

## mega.StoItemQtyFreeExQud.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemQtyFreeExQud_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Products on store with availability and next ship (itemized by QudId).

## mega.StoItemQtyFreeExQud.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemQtyFreeExQud_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Products on store with availability and next ship (itemized by QudId).

## mega.StoItemQtyFreeExQudT.delta

- Excluded from client calls (`blocked`).
- Evidence: Products on store with availability and next ship (sum of all user's stores).

## mega.StoItemQtyFreeExQudT.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemQtyFreeExQudT_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Products on store with availability and next ship (sum of all user's stores).

## mega.StoItemQtyFreeExQudT.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemQtyFreeExQudT_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Products on store with availability and next ship (sum of all user's stores).

## mega.StoItemQtyFreeExQudT_El.delta

- Excluded from client calls (`blocked`).
- Evidence: Products on store with availability and next ship (sum of all user's stores).

## mega.StoItemQtyFreeExQudT_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemQtyFreeExQudT_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Products on store with availability and next ship (sum of all user's stores).

## mega.StoItemQtyFreeExQudT_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemQtyFreeExQudT_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Products on store with availability and next ship (sum of all user's stores).

## mega.StoItemQtyFreeExQud_El.delta

- Excluded from client calls (`blocked`).
- Evidence: Products on store with availability and next ship (itemized by QudId).

## mega.StoItemQtyFreeExQud_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemQtyFreeExQud_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Products on store with availability and next ship (itemized by QudId).

## mega.StoItemQtyFreeExQud_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemQtyFreeExQud_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Products on store with availability and next ship (itemized by QudId).

## mega.StoItemQtyFreeEx_El.delta

- Excluded from client calls (`blocked`).
- Evidence: Products on store with availability and next ship.

## mega.StoItemQtyFreeEx_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemQtyFreeEx_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Products on store with availability and next ship.

## mega.StoItemQtyFreeEx_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemQtyFreeEx_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Products on store with availability and next ship.

## mega.StoItemQtyFree_El.delta

- Excluded from client calls (`blocked`).
- Evidence: Products on store.

## mega.StoItemQtyFree_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemQtyFree_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Products on store.

## mega.StoItemQtyFree_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemQtyFree_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 22, 23.
- Evidence: Products on store.

## mega.StoItemShop_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `StoItemShop_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Base informations about products - shop feed.

## mega.StoItemShop_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemShop_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Base informations about products - shop feed.

## mega.StoItemShop_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemShop_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Base informations about products - shop feed.

## mega.StoItemShoptet_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `StoItemShoptet_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Base informations about products - Shoptet feed.

## mega.StoItemShoptet_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemShoptet_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Base informations about products - Shoptet feed.

## mega.StoItemShoptet_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemShoptet_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Base informations about products - Shoptet feed.

## mega.StoItemSiv.delta

- Excluded from client calls (`blocked`).
- Evidence: Export for I6 module StoItemCom.

## mega.StoItemSiv.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemSiv_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Export for I6 module StoItemCom.

## mega.StoItemSiv.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemSiv_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export for I6 module StoItemCom.

## mega.StoItemSiv_El.delta

- Excluded from client calls (`blocked`).
- Evidence: Export for I6 module StoItemCom.

## mega.StoItemSiv_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `StoItemSiv_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Export for I6 module StoItemCom.

## mega.StoItemSiv_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StoItemSiv_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export for I6 module StoItemCom.

## mega.StrStiSync.delta

- Excluded from client calls (`blocked`).
- Evidence: Export for synchronisation of SPresentTree + StoItem. As code must be send id of SPresentTree.

## mega.StrStiSync.full

- Excluded from client calls (`blocked`).
- Evidence: Export for synchronisation of SPresentTree + StoItem. As code must be send id of SPresentTree.

## mega.StrStiSync.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StrStiSync_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Export for synchronisation of SPresentTree + StoItem. As code must be send id of SPresentTree.

## mega.StrStiSync_El.delta

- Excluded from client calls (`blocked`).
- Evidence: Export for synchronisation of SPresentTree + StoItem. As code must be send id of SPresentTree.

## mega.StrStiSync_El.full

- Excluded from client calls (`blocked`).
- Evidence: Export for synchronisation of SPresentTree + StoItem. As code must be send id of SPresentTree.

## mega.StrStiSync_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `StrStiSync_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Export for synchronisation of SPresentTree + StoItem. As code must be send id of SPresentTree.

## mega.X-100M.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-100M_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Special export for 100M

## mega.X-100M.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-100M_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Special export for 100M

## mega.X-100M.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-100M_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Special export for 100M

## mega.X-100M_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-100M_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Special export for 100M

## mega.X-100M_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-100M_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Special export for 100M

## mega.X-100M_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-100M_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Special export for 100M

## mega.X-ASM-CpsStiVal.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-ASM-CpsStiVal_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export parameters of StoItems - Name x Value only (filtered by Code of StoItem).

## mega.X-ASM-CpsStiVal.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-ASM-CpsStiVal_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export parameters of StoItems - Name x Value only (filtered by Code of StoItem).

## mega.X-ASM-CpsStiVal.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-ASM-CpsStiVal_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export parameters of StoItems - Name x Value only (filtered by Code of StoItem).

## mega.X-ASM-CpsStiVal_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-ASM-CpsStiVal_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export parameters of StoItems - Name x Value only (filtered by Code of StoItem).

## mega.X-ASM-CpsStiVal_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-ASM-CpsStiVal_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export parameters of StoItems - Name x Value only (filtered by Code of StoItem).

## mega.X-ASM-CpsStiVal_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-ASM-CpsStiVal_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export parameters of StoItems - Name x Value only (filtered by Code of StoItem).

## mega.X-ASM-StiRelation.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-ASM-StiRelation_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export souvisejících produktů pro ASM zboží

## mega.X-ASM-StiRelation.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-ASM-StiRelation_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export souvisejících produktů pro ASM zboží

## mega.X-ASM-StiRelation.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-ASM-StiRelation_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export souvisejících produktů pro ASM zboží

## mega.X-ASM-StiRelation_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-ASM-StiRelation_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export souvisejících produktů pro ASM zboží

## mega.X-ASM-StiRelation_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-ASM-StiRelation_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export souvisejících produktů pro ASM zboží

## mega.X-ASM-StiRelation_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-ASM-StiRelation_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export souvisejících produktů pro ASM zboží

## mega.X-ASM-StoItemSiv.delta

- Excluded from client calls (`blocked`).
- Evidence: Export for I6 module StoItemCom.

## mega.X-ASM-StoItemSiv.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-ASM-StoItemSiv_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Export for I6 module StoItemCom.

## mega.X-ASM-StoItemSiv.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-ASM-StoItemSiv_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export for I6 module StoItemCom.

## mega.X-ASM-StoItemSiv_El.delta

- Excluded from client calls (`blocked`).
- Evidence: Export for I6 module StoItemCom.

## mega.X-ASM-StoItemSiv_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-ASM-StoItemSiv_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Export for I6 module StoItemCom.

## mega.X-ASM-StoItemSiv_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-ASM-StoItemSiv_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export for I6 module StoItemCom.

## mega.X-CpsStiVal.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-CpsStiVal_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export parameters of StoItems - Name x Value only (filtered by Code of StoItem).

## mega.X-CpsStiVal.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-CpsStiVal_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export parameters of StoItems - Name x Value only (filtered by Code of StoItem).

## mega.X-CpsStiVal.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-CpsStiVal_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export parameters of StoItems - Name x Value only (filtered by Code of StoItem).

## mega.X-CpsStiVal_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-CpsStiVal_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export parameters of StoItems - Name x Value only (filtered by Code of StoItem).

## mega.X-CpsStiVal_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-CpsStiVal_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export parameters of StoItems - Name x Value only (filtered by Code of StoItem).

## mega.X-CpsStiVal_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-CpsStiVal_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export parameters of StoItems - Name x Value only (filtered by Code of StoItem).

## mega.X-Cybex.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-Cybex_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Special export for Cybex.

## mega.X-Cybex.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-Cybex_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Special export for Cybex.

## mega.X-Cybex.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-Cybex_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Special export for Cybex.

## mega.X-Cybex_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-Cybex_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Special export for Cybex.

## mega.X-Cybex_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-Cybex_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Special export for Cybex.

## mega.X-Cybex_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-Cybex_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Special export for Cybex.

## mega.X-EAN.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-EAN_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export EAN produktu

## mega.X-EAN.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-EAN_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export EAN produktu

## mega.X-EAN.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-EAN_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export EAN produktu

## mega.X-EAN_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-EAN_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export EAN produktu

## mega.X-EAN_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-EAN_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export EAN produktu

## mega.X-EAN_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-EAN_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export EAN produktu

## mega.X-EnterpriceB2C.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-EnterpriceB2C_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Account index identifies a B2C product export.

## mega.X-EnterpriceB2C.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-EnterpriceB2C_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Account index identifies a B2C product export.

## mega.X-EnterpriceB2C.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-EnterpriceB2C_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Account index identifies a B2C product export.

## mega.X-EnterpriceB2C_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-EnterpriceB2C_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Account index identifies a B2C product export.

## mega.X-EnterpriceB2C_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-EnterpriceB2C_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Account index identifies a B2C product export.

## mega.X-EnterpriceB2C_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-EnterpriceB2C_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Account index identifies a B2C product export.

## mega.X-HOG.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-HOG_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Special export for HoG

## mega.X-HOG.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-HOG_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Special export for HoG

## mega.X-HOG.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-HOG_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Special export for HoG

## mega.X-HOG_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-HOG_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Special export for HoG

## mega.X-HOG_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-HOG_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Special export for HoG

## mega.X-HOG_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-HOG_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Special export for HoG

## mega.X-HalshopDayOffer.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-HalshopDayOffer_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export nabidky dne

## mega.X-HalshopDayOffer.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-HalshopDayOffer_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export nabidky dne

## mega.X-HalshopDayOffer.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-HalshopDayOffer_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export nabidky dne

## mega.X-HalshopDayOffer_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-HalshopDayOffer_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export nabidky dne

## mega.X-HalshopDayOffer_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-HalshopDayOffer_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export nabidky dne

## mega.X-HalshopDayOffer_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-HalshopDayOffer_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export nabidky dne

## mega.X-LMStiPacking.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-LMStiPacking_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of length, width, height, weight of items.

## mega.X-LMStiPacking.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-LMStiPacking_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of length, width, height, weight of items.

## mega.X-LMStiPacking.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-LMStiPacking_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of length, width, height, weight of items.

## mega.X-LMStiPacking_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-LMStiPacking_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of length, width, height, weight of items.

## mega.X-LMStiPacking_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-LMStiPacking_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of length, width, height, weight of items.

## mega.X-LMStiPacking_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-LMStiPacking_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of length, width, height, weight of items.

## mega.X-Retail.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-Retail_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Order prices in user's currency, included EAN code.

## mega.X-Retail.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-Retail_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Order prices in user's currency, included EAN code.

## mega.X-Retail.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-Retail_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Order prices in user's currency, included EAN code.

## mega.X-Retail_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-Retail_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Order prices in user's currency, included EAN code.

## mega.X-Retail_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-Retail_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Order prices in user's currency, included EAN code.

## mega.X-Retail_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-Retail_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Order prices in user's currency, included EAN code.

## mega.X-StoItemClass.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-StoItemClass_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Tridy produktu

## mega.X-StoItemClass.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-StoItemClass_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Tridy produktu

## mega.X-StoItemClass.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-StoItemClass_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Tridy produktu

## mega.X-StoItemClass_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-StoItemClass_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Tridy produktu

## mega.X-StoItemClass_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-StoItemClass_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Tridy produktu

## mega.X-StoItemClass_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-StoItemClass_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export Tridy produktu

## mega.X-StoItemPack.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-StoItemPack_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export tabulky StoItemPack

## mega.X-StoItemPack.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-StoItemPack_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export tabulky StoItemPack

## mega.X-StoItemPack.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-StoItemPack_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export tabulky StoItemPack

## mega.X-StoItemPack_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-StoItemPack_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export tabulky StoItemPack

## mega.X-StoItemPack_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-StoItemPack_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export tabulky StoItemPack

## mega.X-StoItemPack_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-StoItemPack_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export tabulky StoItemPack

## mega.X-StoItemPriceEU.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-StoItemPriceEU_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of End User's prices.

## mega.X-StoItemPriceEU.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-StoItemPriceEU_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of End User's prices.

## mega.X-StoItemPriceEU.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-StoItemPriceEU_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of End User's prices.

## mega.X-StoItemPriceEU_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-StoItemPriceEU_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of End User's prices.

## mega.X-StoItemPriceEU_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-StoItemPriceEU_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of End User's prices.

## mega.X-StoItemPriceEU_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-StoItemPriceEU_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of End User's prices.

## mega.X-StoItemPriceOrdCur.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-StoItemPriceOrdCur_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Order prices in user's currency, included EAN code.

## mega.X-StoItemPriceOrdCur.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-StoItemPriceOrdCur_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Order prices in user's currency, included EAN code.

## mega.X-StoItemPriceOrdCur.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-StoItemPriceOrdCur_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Order prices in user's currency, included EAN code.

## mega.X-StoItemPriceOrdCur_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-StoItemPriceOrdCur_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Order prices in user's currency, included EAN code.

## mega.X-StoItemPriceOrdCur_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-StoItemPriceOrdCur_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Order prices in user's currency, included EAN code.

## mega.X-StoItemPriceOrdCur_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-StoItemPriceOrdCur_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Order prices in user's currency, included EAN code.

## mega.X-StoItemVariant.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-StoItemVariant_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export variant produktu

## mega.X-StoItemVariant.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-StoItemVariant_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export variant produktu

## mega.X-StoItemVariant.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-StoItemVariant_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export variant produktu

## mega.X-StoItemVariant_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-StoItemVariant_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export variant produktu

## mega.X-StoItemVariant_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-StoItemVariant_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export variant produktu

## mega.X-StoItemVariant_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-StoItemVariant_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export variant produktu

## mega.X-StoItemWoutNote.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-StoItemWoutNote_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Base informations about products without Note.

## mega.X-StoItemWoutNote.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-StoItemWoutNote_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Base informations about products without Note.

## mega.X-StoItemWoutNote.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-StoItemWoutNote_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Base informations about products without Note.

## mega.X-StoItemWoutNote_El.delta

- Scope: `catalog:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `X-StoItemWoutNote_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Base informations about products without Note.

## mega.X-StoItemWoutNote_El.full

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `X-StoItemWoutNote_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 21, 22, 23.
- Evidence: Base informations about products without Note.

## mega.X-StoItemWoutNote_El.targeted

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `X-StoItemWoutNote_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Base informations about products without Note.

## mega.ZCompany.delta

- Scope: `documents:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `ZCompany_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of B2C users.

## mega.ZCompany.full

- Scope: `documents:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ZCompany_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of B2C users.

## mega.ZCompany.targeted

- Scope: `documents:read`
- Supplier inputs: `code: string`
- Output: `ZCompany_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of B2C users.

## mega.ZCompany_El.delta

- Scope: `documents:read`
- Supplier inputs: `from: dateTime`, `to: dateTime`
- Output: `ZCompany_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of B2C users.

## mega.ZCompany_El.full

- Scope: `documents:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ZCompany_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of B2C users.

## mega.ZCompany_El.targeted

- Scope: `documents:read`
- Supplier inputs: `code: string`
- Output: `ZCompany_El_Schema`
- Allowed by reviewed contract: days 1, 2, 3, 4, 5, 6, 7; hours 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.
- Evidence: Export of B2C users.

## mega.ZShop.delta

- Excluded from client calls (`blocked`).
- Evidence: ZShop settings. Settings may include secrets; output fields are unverified.

## mega.ZShop.full

- Excluded from client calls (`blocked`).
- Evidence: ZShop settings. Settings may include secrets; output fields are unverified.

## mega.ZShop.targeted

- Excluded from client calls (`blocked`).
- Evidence: ZShop settings. Settings may include secrets; output fields are unverified.

## mega.ZShop_El.delta

- Excluded from client calls (`blocked`).
- Evidence: ZShop settings. Settings may include secrets; output fields are unverified.

## mega.ZShop_El.full

- Excluded from client calls (`blocked`).
- Evidence: ZShop settings. Settings may include secrets; output fields are unverified.

## mega.ZShop_El.targeted

- Excluded from client calls (`blocked`).
- Evidence: ZShop settings. Settings may include secrets; output fields are unverified.
