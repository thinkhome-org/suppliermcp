# 100MEGA Order.asmx

Generated from the reviewed runtime registry. Use the exact operation ID with the Python, REST or MCP interface. An input ending in ? is optional in the supplier contract. The service may enforce stricter input rules for a safe read.

[Calling and paging](operation-reads.md) · [Live acceptance](v2-acceptance.md)

## mega_order.AppendNoteIntText

- Excluded from client calls (`write`).
- Evidence: mega_order WSDL: Append text into internal Note of existing order.

## mega_order.AppendNoteText

- Excluded from client calls (`write`).
- Evidence: mega_order WSDL: Append text into Note of existing order.

## mega_order.AppendStoItem

- Excluded from client calls (`write`).
- Evidence: mega_order WSDL: Append StoItem into existing order.

## mega_order.CancelItem

- Excluded from client calls (`write`).
- Evidence: mega_order WSDL: Cancel item from existing order - If not OrdItemQty > 0 then all ordered qty is canceled.

## mega_order.CancelStoItem

- Excluded from client calls (`write`).
- Evidence: mega_order WSDL: Complet cancel StoItem (+ all related StoItem(s)) from existing order.

## mega_order.Create

- Excluded from client calls (`write`).
- Evidence: mega_order WSDL: Create Order.

## mega_order.CreateComShipTo

- Excluded from client calls (`write`).
- Evidence: mega_order WSDL: Create (or update - with existing id) ComShipTo.

## mega_order.CreateComShipToXCompanyId

- Excluded from client calls (`write`).
- Evidence: mega_order WSDL: Create ComShipTo on specified XCompanyId.

## mega_order.CreateLoginTag

- Excluded from client calls (`write`).
- Evidence: mega_order WSDL: Create LoginTag for disposable special access.

## mega_order.CreatePOL

- Excluded from client calls (`write`).
- Evidence: mega_order WSDL: Create POL (Payment online).

## mega_order.CreateParameters

- Excluded from client calls (`write`).
- Evidence: mega_order WSDL: Create Order Parameters.

## mega_order.CreateXCompany

- Excluded from client calls (`write`).
- Evidence: mega_order WSDL: Create  (or update - with existing id) XCompany (XCompany = Company + Contact[ConType = 1] + Contact[ConType = 2] in same data structure as ZCompany).

## mega_order.ExecuteTrgX

- Excluded from client calls (`blocked`).
- Evidence: mega_order WSDL: Execute named TrgX.

## mega_order.GetComShipTo

- Scope: `documents:read`
- Supplier inputs: `Id: int`
- Output: `ComShipTo`
- Evidence: mega_order WSDL: Return ComShipTo by Id.

## mega_order.GetComShipToListChanged

- Scope: `documents:read`
- Supplier inputs: `ChangeDate: dateTime`
- Output: `ArrayOfComShipTo`
- Evidence: mega_order WSDL: Return List of ComShipTo specified by ChangeDate(CstU).

## mega_order.GetComShipToListId

- Scope: `documents:read`
- Supplier inputs: `IdList: string`
- Output: `ArrayOfComShipTo`
- Evidence: mega_order WSDL: Return List of ComShipTo specified by Id(comma separated, max.

## mega_order.GetStatus

- Scope: `documents:read`
- Supplier inputs: `Id: int`
- Output: `OrderInfo`
- Evidence: mega_order WSDL: Return Status of Order specified by Id.

## mega_order.GetStatusListAppendReady

- Scope: `documents:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ArrayOfOrder`
- Evidence: mega_order WSDL: Return StatusList of Order ready for appending/changing items.

## mega_order.GetStatusListChanged

- Scope: `documents:read`
- Supplier inputs: `ChangeDate: dateTime`
- Output: `ArrayOfOrder`
- Evidence: mega_order WSDL: Return StatusList of Order specified by ChangeDate(OriU,DelU,SopU,ExpDateS).

## mega_order.GetStatusListChangedExpS

- Scope: `documents:read`
- Supplier inputs: `ChangeDateExpS: dateTime`
- Output: `ArrayOfOrder`
- Evidence: mega_order WSDL: Return StatusList of Order specified by ChangeDate(ExpDateS) - optimized for detect changes in expeditions.

## mega_order.GetStatusListCode

- Scope: `documents:read`
- Supplier inputs: `CodeList: string`
- Output: `ArrayOfOrder`
- Evidence: mega_order WSDL: Return StatusList of Order specified by Code(comma separated, max.

## mega_order.GetStatusListCodeO

- Scope: `documents:read`
- Supplier inputs: `CodeOList: string`
- Output: `ArrayOfOrder`
- Evidence: mega_order WSDL: Return StatusList of Order specified by CodeO(comma separated, max.

## mega_order.GetStatusListId

- Scope: `documents:read`
- Supplier inputs: `IdList: string`
- Output: `ArrayOfOrder`
- Evidence: mega_order WSDL: Return StatusList of Order specified by Id(comma separated, max.

## mega_order.GetStatusListOpened

- Scope: `documents:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ArrayOfOrder`
- Evidence: mega_order WSDL: Return StatusList of Order specified by Opened.

## mega_order.GetStatusListTag

- Scope: `documents:read`
- Supplier inputs: `TagList: string`
- Output: `ArrayOfOrder`
- Evidence: mega_order WSDL: Return StatusList of Order specified by Tag(comma separated, max.

## mega_order.GetXCompany

- Scope: `documents:read`
- Supplier inputs: `Id: int`
- Output: `ZCompany`
- Evidence: mega_order WSDL: Return XCompany by Id.

## mega_order.GetXCompanyListChanged

- Scope: `documents:read`
- Supplier inputs: `ChangeDate: dateTime`
- Output: `ArrayOfZCompany`
- Evidence: mega_order WSDL: Return List of XCompany specified by ChangeDate(ComU,ConT1.ConU,ConT2.ConU).

## mega_order.GetXCompanyListId

- Scope: `documents:read`
- Supplier inputs: `IdList: string`
- Output: `ArrayOfZCompany`
- Evidence: mega_order WSDL: Return List of XCompany specified by Id(comma separated, max.

## mega_order.SetOption

- Excluded from client calls (`write`).
- Evidence: mega_order WSDL: Set Option (Name: OrdCode | InvCode | DelCode | InvFooter).
