import os

import httpx
import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from pydantic_core import to_jsonable_python
from test_mcp import running_server

from suppliermcp.access import AccessDenied, Identity
from suppliermcp.catalog.contracts import BatchManifest, Offer, SourceItem
from suppliermcp.config import Settings
from suppliermcp.service import CATALOG_OPERATIONS, CatalogService
from suppliermcp.suppliers.reads import ReadResult, SupplierField
from suppliermcp.suppliers.registry import operation_inventory
from suppliermcp.sync.publish import publish, stage

SCOPES = "catalog:read documents:read"
CLIENTS = {"personal": {"document_subjects": ["alice"]}, "registered": {}}
DOCUMENT = "ed_public.getInvoiceDetail"


def auth(token):
    return {"Authorization": "Bearer " + token}


async def test_catalog_and_document_read_parity(conn, monkeypatch):
    rows = [SourceItem(supplier="ed", source_id=n, sku=n, name="Memory") for n in ("001", "002")]
    rows += [
        Offer(item_id="ed:001", currency="CZK", unit_net="11", fees_net="0", order_multiple="10")
    ]
    publish(conn, stage(conn, BatchManifest(interface="ed_public", domain="catalog"), rows))

    def document_reply(self, spec, arguments):
        assert spec.operation_id == DOCUMENT and arguments["invoiceSymbol"] == "00017"
        return ReadResult(
            operation_id=DOCUMENT,
            output_schema=spec.output_schema,
            fields=[SupplierField(path="invoice/number", value="00017")],
            truncated=False,
        )

    monkeypatch.setattr("suppliermcp.suppliers.reads.OperationReader._read", document_reply)
    settings = Settings(
        database_url=os.getenv(
            "SUPPLIERMCP_TEST_DSN", "postgresql://test:test@localhost:55439/test"
        ),
        page_size=1,
    )
    service = CatalogService(
        settings, Identity("suppliermcp", "alice", "personal", frozenset(SCOPES.split()))
    )
    with running_server(auth_clients=CLIENTS, page_size=1) as (url, sign):
        personal = sign(client_id="personal", scope=SCOPES)
        ordinary = sign(client_id="registered", scope=SCOPES)
        async with (
            httpx.AsyncClient(
                base_url=url.removesuffix("/mcp") + "/v2/", headers=auth(personal)
            ) as http,
            Client(url, auth=personal) as mcp,
        ):
            schema = (await http.get("openapi.json")).json()
            assert {"/catalog/" + name for name in CATALOG_OPERATIONS} <= schema["paths"].keys()
            for name, args in [
                (
                    "lookup_products",
                    {"identifiers": [{"kind": "sku", "supplier": "ed", "value": "001"}]},
                ),
                ("get_product", {"product_id": "ed:001"}),
                ("get_catalog_status", {}),
                ("compare_offers", {"product_ids": ["ed:001"], "quantities": {"ed:001": "12"}}),
            ]:
                expected = to_jsonable_python(await getattr(service, name)(**args))
                assert "error" not in expected
                response = await http.post("catalog/" + name, json=args)
                response.raise_for_status()
                assert response.json() == expected
                assert (await mcp.call_tool(name, args)).structured_content["result"] == expected
            assert expected[0]["offers"][0]["total_net"] == "220"

            page = (await http.post("catalog/list_products", json={})).json()
            assert page["next_cursor"]
            args = {"cursor": page["next_cursor"]}
            async with Client(url, auth=ordinary) as other:
                replay = await other.call_tool("list_products", args)
                assert replay.structured_content["result"]["error"]["code"] == "result_not_found"
            assert (
                await http.post("catalog/list_products", json=args, headers=auth(ordinary))
            ).json()["error"]["code"] == "result_not_found"

            args = {"invoiceSymbol": "00017"}
            path = f"operations/{DOCUMENT}/read"
            expected_doc = (await service.read_operation(DOCUMENT, args)).model_dump(mode="json")
            assert expected_doc["fields"][0]["value"] == "00017"
            assert (await http.post(path, json=args)).json() == expected_doc
            assert (
                await mcp.call_tool("read_operation", {"operation_id": DOCUMENT, "arguments": args})
            ).structured_content == expected_doc
            assert (await http.post(path, json=args, headers=auth(ordinary))).status_code == 403
            async with Client(url, auth=ordinary) as other:
                with pytest.raises(ToolError, match="forbidden"):
                    await other.call_tool(
                        "read_operation", {"operation_id": DOCUMENT, "arguments": args}
                    )
            ordinary_service = CatalogService(
                settings,
                Identity("suppliermcp", "alice", "registered", frozenset({"catalog:read"})),
            )
            with pytest.raises(AccessDenied) as error:
                await ordinary_service.read_operation(DOCUMENT, args)
            assert error.value.status_code == 403
            assert (
                await http.post(path, json=args, headers={"Authorization": ""})
            ).status_code == 401


async def test_every_reviewed_operation_is_discoverable_and_validated():
    expected = {spec.operation_id for spec in operation_inventory() if spec.effect == "read"}
    with running_server(auth_clients=CLIENTS) as (url, sign):
        token = sign(client_id="personal", scope=SCOPES)
        async with (
            httpx.AsyncClient(
                base_url=url.removesuffix("/mcp") + "/v2/", headers=auth(token)
            ) as http,
            Client(url, auth=token) as mcp,
        ):
            found = []
            offset = 0
            while offset is not None:
                page = (await http.get("operations", params={"offset": offset})).json()
                assert (
                    await mcp.call_tool("list_operations", {"offset": offset})
                ).structured_content == page
                found.extend(row["operation_id"] for row in page["operations"])
                offset = page["next_offset"]
            assert len(found) == len(expected) and set(found) == expected
            for name in found:
                arguments = {"unexpected_secret": "sensitive-value"}
                response = await http.post(f"operations/{name}/read", json=arguments)
                assert (
                    response.status_code == 400
                    and response.json()["error"]["code"] == "invalid_arguments"
                )
                assert "sensitive-value" not in response.text
                with pytest.raises(ToolError, match="invalid_arguments"):
                    await mcp.call_tool(
                        "read_operation", {"operation_id": name, "arguments": arguments}
                    )


async def test_remote_continuations_reach_shared_reader(monkeypatch):
    async def read(self, identity, operation_id, arguments, *, cursor):
        assert identity.subject == "alice" and operation_id == DOCUMENT
        assert arguments == {"invoiceSymbol": "00017"}
        return ReadResult(
            operation_id=operation_id,
            output_schema="invoice",
            fields=[SupplierField(path="cursor", value=cursor)],
            truncated=False,
        )

    monkeypatch.setattr("suppliermcp.suppliers.reads.OperationReader.read_operation", read)
    with running_server(auth_clients=CLIENTS) as (url, sign):
        token = sign(client_id="personal", scope=SCOPES)
        args = {"invoiceSymbol": "00017"}
        async with httpx.AsyncClient(headers=auth(token)) as http, Client(url, auth=token) as mcp:
            response = await http.post(
                url.removesuffix("/mcp") + f"/v2/operations/{DOCUMENT}/read",
                headers={"X-Read-Cursor": "opaque"},
                json=args,
            )
            assert response.json()["fields"][0]["value"] == "opaque"
            result = await mcp.call_tool(
                "read_operation", {"operation_id": DOCUMENT, "arguments": args, "cursor": "opaque"}
            )
            assert result.structured_content == response.json()
