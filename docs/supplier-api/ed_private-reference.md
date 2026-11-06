# eD PRIVATE

Generated from the reviewed runtime registry. Use the exact operation ID with the Python, REST or MCP interface. An input ending in ? is optional in the supplier contract. The service may enforce stricter input rules for a safe read.

[Calling and paging](operation-reads.md) · [Live acceptance](v2-acceptance.md)

## ed_private.changeDocument

- Excluded from client calls (`write`).
- Evidence: ed_private WSDL: Makes changes to the document.

## ed_private.createNewOrder

- Excluded from client calls (`write`).
- Evidence: ed_private WSDL: Create order to system by this method.

## ed_private.createNewOrderCustomer

- Excluded from client calls (`write`).
- Evidence: ed_private WSDL: Create order to system by this method.

## ed_private.createNewOrderXML

- Excluded from client calls (`write`).
- Evidence: ed_private WSDL: Create order to system by this method.

## ed_private.getNavigator

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ResponseProductNavigator`
- Evidence: ed_private WSDL: Get product navigator data.

## ed_private.getProductCatalogueDownloadXML

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ResponseProductListStatus`
- Evidence: ed_private WSDL: Download whole product catalogue as XML file.

## ed_private.getProductCatalogueDownloadZIP

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ResponseProductListStatus`
- Evidence: ed_private WSDL: Download whole product catalogue as ZIP file.

## ed_private.getProductCatalogueFullDownloadXML

- Scope: `catalog:read`
- Supplier inputs: `onStock: boolean`, `Comodities?: string`
- Output: `ResponseProductListStatus`
- Evidence: ed_private WSDL: Get URL for download product list as XML file.

## ed_private.getProductCatalogueFullDownloadXMLExt

- Scope: `catalog:read`
- Supplier inputs: `onStock: boolean`, `Comodities?: string`, `Producers?: string`, `Categories?: string`
- Output: `ResponseProductListStatus`
- Evidence: ed_private WSDL: Get URL for download product list as XML file.

## ed_private.getProductCatalogueFullDownloadXMLWithTransform

- Excluded from client calls (`blocked`).
- Evidence: PRIVATE PDF section 3.18 marks this method unimplemented.

## ed_private.getProductCatalogueFullDownloadXMLv1

- Scope: `catalog:read`
- Supplier inputs: `onStock: boolean`, `Comodities?: string`, `ComoditiesTree?: string`, `Producers?: string`, `Categories?: string`
- Output: `ResponseProductListStatus`
- Evidence: ed_private WSDL: Get URL for download product list as XML file.

## ed_private.getProductCatalogueFullDownloadZIP

- Scope: `catalog:read`
- Supplier inputs: `onStock: boolean`, `Comodities?: string`
- Output: `ResponseProductListStatus`
- Evidence: ed_private WSDL: Get URL for download product list as zipped XML file.

## ed_private.getProductCatalogueFullDownloadZIPExt

- Scope: `catalog:read`
- Supplier inputs: `onStock: boolean`, `Comodities?: string`, `Producers?: string`, `Categories?: string`
- Output: `ResponseProductListStatus`
- Evidence: ed_private WSDL: Get URL for download product list as zipped XML file.

## ed_private.getProductCatalogueFullDownloadZIPv1

- Scope: `catalog:read`
- Supplier inputs: `onStock: boolean`, `Comodities?: string`, `ComoditiesTree?: string`, `Producers?: string`, `Categories?: string`
- Output: `ResponseProductListStatus`
- Evidence: ed_private WSDL: Get URL for download product list as zipped XML file.

## ed_private.getProductCatalogueFullNavFilterDownloadXML

- Scope: `catalog:read`
- Supplier inputs: `onStock: boolean`, `navigatorFilter?: string`
- Output: `ResponseProductListStatus`
- Evidence: ed_private WSDL: Get URL for download product list as XML file according to product navigator filter definition.

## ed_private.getProductCatalogueFullNavFilterSOAPDownloadXML

- Scope: `catalog:read`
- Supplier inputs: `onStock: boolean`, `filter?: ProductNavigatorFilter`
- Output: `ResponseProductListStatus`
- Evidence: ed_private WSDL: Get URL for download product list as XML file according to product navigator filter definition.

## ed_private.getProductCatalogueFullPremiumDownloadXML

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ResponseProductListStatus`
- Evidence: ed_private WSDL: Get URL for download premium product list as XML file.

## ed_private.getProductCatalogueShortDownloadXML

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ResponseProductListStatus`
- Evidence: ed_private WSDL: Download whole product catalogue with basic information as XML file.

## ed_private.getProductCatalogueStockDownloadXML

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ResponseProductListStatus`
- Evidence: ed_private WSDL: Download whole product catalogue with stock information as XML file.

## ed_private.getProductCategoryAttributeList

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ResponseProductCategoryAttributeList`
- Evidence: ed_private WSDL: Get list of attributes.

## ed_private.getProductCategoryAttributeValueList

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ResponseProductCategoryAttributeValueList`
- Evidence: ed_private WSDL: Get list of possible attribute values of attributes.

## ed_private.getProductCategoryList

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ResponseProductCategoryList`
- Evidence: ed_private WSDL: Get list of categories.

## ed_private.getProductCommodityList

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ResponseProductCommodityList`
- Evidence: ed_private WSDL: Get list of commodities.

## ed_private.getProductDetail

- Scope: `catalog:read`
- Supplier inputs: `code: string`
- Output: `ResponseProductComplete`
- Evidence: ed_private WSDL: Get detailed description of a product as SOAP.

## ed_private.getProductIndexTree1

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ResponseProductIndexTree`
- Evidence: ed_private WSDL: Get product index tree 1.

## ed_private.getProductIndexTree2

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ResponseProductIndexTree`
- Evidence: ed_private WSDL: Get product index tree 2.

## ed_private.getProductInformationList

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ResponseProductInformationList`
- Evidence: ed_private WSDL: Get product information list.

## ed_private.getProductProducerList

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ResponseProductProducerList`
- Evidence: ed_private WSDL: Get list of producers.

## ed_private.getProductRelationList

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ResponseProductRelationList`
- Evidence: ed_private WSDL: Relations between products (Accessory,Replacement).

## ed_private.getProductSuperCategoryList

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ResponseProductSuperCategoryList`
- Evidence: ed_private WSDL: Get list of supercatagories with categories.

## ed_private.getTransportationList

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ResponseTransportationList`
- Evidence: ed_private WSDL: Get list of transportations.

## ed_private.getTransportationListCustomer

- Scope: `catalog:read`
- Supplier inputs: none beyond server-side authentication
- Output: `ResponseTransportationList`
- Evidence: ed_private WSDL: Get list of transportations suitable for B2C.
