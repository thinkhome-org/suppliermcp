# eD PUBLIC

Generated from the reviewed runtime registry. Use the exact operation ID with the Python, REST or MCP interface. An input ending in ? is optional in the supplier contract. The service may enforce stricter input rules for a safe read.

[Calling and paging](operation-reads.md) · [Live acceptance](v2-acceptance.md)

## ed_public.getAuthTokenEshop

- Excluded from client calls (`blocked`).
- Evidence: ed_public WSDL: Get authentication data for eshop.

## ed_public.getClaimList

- Scope: `documents:read`
- Supplier inputs: `dateFrom: string`, `dateTo?: string`
- Output: `ResponseClaimList`
- Evidence: ed_public WSDL: Get list od claims for specified perriod as SOAP.

## ed_public.getDeliveryDetail

- Scope: `documents:read`
- Supplier inputs: `deliverySymbol: string`
- Output: `ResponseDeliveryDetail`
- Evidence: ed_public WSDL: Get delivery note detail as SOAP.

## ed_public.getDeliveryList

- Scope: `documents:read`
- Supplier inputs: `dateFrom: string`, `dateTo?: string`
- Output: `ResponseDeliveryList`
- Evidence: ed_public WSDL: Get list of delivery notes for specified perriod as SOAP.

## ed_public.getExpeditionDetail

- Scope: `documents:read`
- Supplier inputs: `expeditionSymbol: string`
- Output: `ResponseExpeditionDetail`
- Evidence: ed_public WSDL: Get delivery detail as SOAP.

## ed_public.getExpeditionList

- Scope: `documents:read`
- Supplier inputs: `dateFrom: string`, `dateTo?: string`
- Output: `ResponseExpeditionList`
- Evidence: ed_public WSDL: Get list od delivery for specified perriod as SOAP.

## ed_public.getInvoiceDetail

- Scope: `documents:read`
- Supplier inputs: `invoiceSymbol: string`
- Output: `ResponseInvoiceDetail`
- Evidence: ed_public WSDL: Get invoice detail as SOAP.

## ed_public.getInvoiceDetailDownloadXMLWithTransform

- Scope: `documents:read`
- Supplier inputs: `invoiceSymbol: string`, `transformation?: string`, `encoding?: string`
- Output: `ResponseInvoiceStatus`
- Evidence: ed_public WSDL: Get invoice detail as XML file.

## ed_public.getInvoiceList

- Scope: `documents:read`
- Supplier inputs: `dateFrom: string`, `dateTo?: string`
- Output: `ResponseInvoiceList`
- Evidence: ed_public WSDL: Get invoices list for specified perriod as SOAP.

## ed_public.getInvoiceListDownloadXMLWithTransform_INT

- Excluded from client calls (`blocked`).
- Evidence: ed_public WSDL: Internal method.

## ed_public.getOrderDetail

- Scope: `documents:read`
- Supplier inputs: `orderSymbol: string`
- Output: `ResponseOrderDetail`
- Evidence: ed_public WSDL: Get order detail as SOAP.

## ed_public.getOrderList

- Scope: `documents:read`
- Supplier inputs: `dateFrom: string`, `dateTo?: string`
- Output: `ResponseOrderList`
- Evidence: ed_public WSDL: Get orders list for specified perriod as SOAP.

## ed_public.getOrderListDownloadXMLWithTransform_INT

- Excluded from client calls (`blocked`).
- Evidence: ed_public WSDL: Internal method.

## ed_public.getProductList

- Scope: `catalog:read`
- Supplier inputs: `onStock: boolean`
- Output: `ResponseProductList`
- Evidence: ed_public WSDL: Get product list as SOAP.

## ed_public.getProductListDownloadXML

- Scope: `catalog:read`
- Supplier inputs: `encoding?: string`, `onStock: boolean`
- Output: `ResponseProductListStatus`
- Evidence: ed_public WSDL: Get product list as XML file.

## ed_public.getProductListDownloadXMLWithTransform

- Scope: `catalog:read`
- Supplier inputs: `transformation?: string`, `encoding?: string`, `onStock: boolean`, `fileFormat?: string`
- Output: `ResponseProductListStatus`
- Evidence: ed_public WSDL: Get product list as XML file.

## ed_public.getProductListDownloadZIP

- Scope: `catalog:read`
- Supplier inputs: `encoding?: string`, `onStock: boolean`
- Output: `ResponseProductListStatus`
- Evidence: ed_public WSDL: Get product list as ZIP file.

## ed_public.getProductListDownloadZIPWithTransform

- Scope: `catalog:read`
- Supplier inputs: `transformation?: string`, `encoding?: string`, `onStock: boolean`, `fileFormat?: string`, `soldItemsOnly: boolean`
- Output: `ResponseProductListStatus`
- Evidence: ed_public WSDL: Get product list as ZIP file.

## ed_public.getSellerInfo

- Scope: `documents:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ResponseSubjectIdentification`
- Evidence: ed_public WSDL: Get identification of seller.
