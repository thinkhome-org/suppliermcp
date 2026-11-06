import io
import zipfile
from datetime import UTC, datetime

import httpx
import pytest

from suppliermcp.access import Identity
from suppliermcp.catalog.contracts import CatalogError
from suppliermcp.config import Settings
from suppliermcp.suppliers.mega.capabilities import account_binding
from suppliermcp.suppliers.reads import OperationReader
from suppliermcp.suppliers.registry import operation_inventory
from suppliermcp.suppliers.transport import SupplierTransport

IDENTITY = Identity("iss", "user", "client", frozenset({"catalog:read", "documents:read"}))
READS = [s for s in operation_inventory() if s.effect == "read"]
SOAP = "http://schemas.xmlsoap.org/soap/envelope/"


def make_reader(handler, spec, tmp_path):
    settings = Settings(
        credentials={k: ("login", "password") for k in ("ed_public", "ed_private", "mega")},
        artifact_dir=tmp_path,
    )

    def factory(*args, **kwargs):
        return SupplierTransport(
            *args,
            **kwargs,
            client=httpx.Client(transport=httpx.MockTransport(handler)),
            resolver=lambda _: ["8.8.8.8"],
            sleep=lambda _: None,
        )

    now = datetime(2026, 11, 2, 0, tzinfo=UTC)
    if spec.days:
        from zoneinfo import ZoneInfo

        now = datetime(2026, 11, 1 + spec.days[0], spec.hours[0], tzinfo=ZoneInfo("Europe/Prague"))
    reader = OperationReader(settings, transport_factory=factory, clock=lambda: now)
    if spec.interface == "mega":
        reader.contracts = {
            "mega": {
                "account_login_sha256": account_binding("login"),
                "exports": {
                    spec.name: {
                        "modes": [spec.mode],
                        "days": [d - 1 for d in spec.days],
                        "hours": spec.hours,
                        "timezone": "Europe/Prague",
                    }
                },
            }
        }
    return reader


def arguments(spec):
    values = {
        "boolean": False,
        "int": 1,
        "string": "X",
        "dateTime": "2026-10-27T13:30:00+01:00",
        "ProductNavigatorFilter": {},
    }
    result = {
        f.name: values[f.xsd_type] for f in spec.inputs if f.required or f.name.endswith("Symbol")
    }
    for k, v in {
        "transformation": "ISDOC_6" if "Invoice" in spec.name else "EDLINKOLDXML",
        "fileFormat": "XML",
        "Comodities": "TEST",
        "dateFrom": "2026-10-26",
        "dateTo": "2026-10-27",
        "to": "2026-10-28T13:30:00+01:00",
    }.items():
        if k in {f.name for f in spec.inputs}:
            result[k] = v
    return result


@pytest.mark.parametrize("spec", READS, ids=lambda s: s.operation_id)
async def test_registered_read_success_empty_and_error(spec, tmp_path, caplog):
    def response(request):
        if request.method == "GET" and spec.strategy == "download":
            data = b"<Items><Item>sample</Item></Items>"
            if "ZIP" in spec.name:
                stream = io.BytesIO()
                with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as z:
                    z.writestr("items.xml", data)
                data = stream.getvalue()
            return httpx.Response(200, content=data)
        if spec.interface == "mega":
            data = f"<Result>{payload}</Result>"
        else:
            ns = spec.action.removesuffix(spec.name)
            if spec.interface.startswith("ed_"):
                ns = ns.rstrip("/")
            data = f'<{spec.name}Result xmlns="{ns}">{payload}</{spec.name}Result>'
            if spec.interface.startswith("ed_"):
                data = f'<{spec.name}Response xmlns="{ns}">{data}</{spec.name}Response>'
            data = f'<s:Envelope xmlns:s="{SOAP}"><s:Body>{data}</s:Body></s:Envelope>'
        return httpx.Response(200, content=data.encode())

    reader = make_reader(response, spec, tmp_path)
    payload = "<StatusCode>ERROR</StatusCode><ErrorText>SENSITIVE_SYNTHETIC</ErrorText>"
    with pytest.raises(CatalogError, match="supplier_response_error"):
        await reader.read_operation(IDENTITY, spec.operation_id, arguments(spec))
    for payload in ("<Item>sample</Item>", ""):
        if spec.strategy == "download":
            payload = (
                "<IsReady>true</IsReady><Url>https://"
                + httpx.URL(spec.target).host
                + "/secret-download</Url>"
            )
        result = await reader.read_operation(IDENTITY, spec.operation_id, arguments(spec))
        assert (
            result.operation_id == spec.operation_id and result.output_schema == spec.output_schema
        )
        assert bool(result.fields) == bool(payload)
    assert "SENSITIVE_SYNTHETIC" not in caplog.text
    assert not list(tmp_path.iterdir())


async def test_deny_before_validation_and_supplier_connection(tmp_path):
    spec = next(s for s in READS if s.operation_id == "mega_order.GetComShipTo")
    reader = make_reader(lambda _: pytest.fail("supplier request"), spec, tmp_path)
    catalog = Identity("issuer", "user", "client", frozenset({"catalog:read"}))
    with pytest.raises(CatalogError, match="forbidden"):
        await reader.read_operation(catalog, spec.operation_id, {"target": "https://evil.invalid"})
    for args in ({"Id": True}, {"Id": 2**31}, {"Id": 1, "password": "x"}, {}):
        with pytest.raises(CatalogError, match="invalid_arguments"):
            await reader.read_operation(IDENTITY, spec.operation_id, args)


async def test_zip_expansion_cap_before_exposing_rows(tmp_path):
    spec = next(s for s in READS if s.operation_id == "ed_public.getProductListDownloadZIP")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("items.xml", b"<Items>" + b" " * 100000 + b"</Items>")

    def handler(request):
        if request.method == "GET":
            return httpx.Response(200, content=buf.getvalue())
        ns = "http://www.elinkx.cz"
        xml = f'<s:Envelope xmlns:s="{SOAP}"><s:Body><{spec.name}Response xmlns="{ns}"><{spec.name}Result><Url>{spec.target}/file</Url></{spec.name}Result></{spec.name}Response></s:Body></s:Envelope>'
        return httpx.Response(200, content=xml.encode())

    reader = make_reader(handler, spec, tmp_path)
    reader.settings.max_expanded_bytes = 4096
    with pytest.raises(CatalogError, match="payload_too_large"):
        await reader.read_operation(IDENTITY, spec.operation_id, arguments(spec))


async def test_reject_wrong_envelope_dtd_and_failure_after_full_preview(tmp_path):
    spec = next(s for s in READS if s.operation_id == "mega.StoItemBase.targeted")
    for xml, code in [
        (b"<html/>", "invalid_supplier_xml"),
        (b"<!DOCTYPE Result><Result/>", "invalid_supplier_xml"),
        (
            b"<Result><Item>" + b"x" * 10000 + b"</Item><StatusCode>ERROR</StatusCode></Result>",
            "supplier_response_error",
        ),
    ]:
        reader = make_reader(lambda _, data=xml: httpx.Response(200, content=data), spec, tmp_path)
        reader.settings.max_response_bytes = 1000
        with pytest.raises(CatalogError, match=code):
            await reader.read_operation(IDENTITY, spec.operation_id, arguments(spec))


async def test_lossless_reader_cursor_for_long_values_and_changed_source(tmp_path):
    spec = next(s for s in READS if s.operation_id == "mega.StoItemBase.targeted")
    value = "\u010desk\u00e9 " * 350
    received = []
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(200, content=f"<Result><Item>{value}</Item></Result>".encode())

    reader = make_reader(handler, spec, tmp_path)
    reader.settings.max_response_bytes = 1000
    args = arguments(spec)
    page = await reader.read_operation(IDENTITY, spec.operation_id, args)
    first = page.next_cursor
    assert page.truncated and first
    wrong = Identity("iss", "user", "second-client", IDENTITY.scopes)
    for owner, arguments_to_use, token in (
        (wrong, args, first),
        (IDENTITY, {"code": "another"}, first),
        (IDENTITY, args, "forged"),
    ):
        with pytest.raises(CatalogError, match="invalid_cursor"):
            await reader.read_operation(owner, spec.operation_id, arguments_to_use, cursor=token)
    assert calls == 1
    while True:
        assert len(page.model_dump_json().encode()) <= 1000
        for field in page.fields:
            assert field.offset == sum(map(len, received))
            received.append(field.value)
        if not page.next_cursor:
            break
        page = await reader.read_operation(
            IDENTITY, spec.operation_id, args, cursor=page.next_cursor
        )
    assert "".join(received) == value
    value += "CHANGED"
    with pytest.raises(CatalogError, match="source_snapshot_changed"):
        await reader.read_operation(IDENTITY, spec.operation_id, args, cursor=first)


async def test_binary_transform_is_reconstructable_across_pages(tmp_path):
    import base64

    data = bytes(range(256)) * 8
    spec = next(
        s for s in READS if s.operation_id == "ed_public.getProductListDownloadXMLWithTransform"
    )

    def handler(request):
        if request.method == "GET":
            return httpx.Response(200, content=data)
        ns = "http://www.elinkx.cz"
        return httpx.Response(
            200,
            content=f'<s:Envelope xmlns:s="{SOAP}"><s:Body><{spec.name}Response xmlns="{ns}"><{spec.name}Result><Url>{spec.target}/file</Url></{spec.name}Result></{spec.name}Response></s:Body></s:Envelope>'.encode(),
        )

    reader = make_reader(handler, spec, tmp_path)
    reader.settings.max_response_bytes = 1400
    cursor = None
    pieces = []
    args = arguments(spec) | {"transformation": "EDLINKXLS", "fileFormat": "XLS"}
    while True:
        page = await reader.read_operation(IDENTITY, spec.operation_id, args, cursor=cursor)
        pieces.extend(f.value for f in page.fields)
        cursor = page.next_cursor
        if not cursor:
            break
    assert base64.b64decode("".join(pieces)) == data


async def test_catalog_projection_blocks_unknown_children_attributes_and_oversized_text(tmp_path):
    spec = next(s for s in READS if s.operation_id == "mega.StoItemBase.targeted")
    poison = "UNREVIEWED_ADDRESS"
    xml = f'<Result><StoItem Code="001" Name="SSD" Address="{poison}"><ShipTo><StoItem Code="{poison}"/><Name>{poison * 300}</Name></ShipTo></StoItem><StoItem Address="{poison}">{poison * 300}</StoItem></Result>'.encode()
    reader = make_reader(lambda _: httpx.Response(200, content=xml), spec, tmp_path)
    owner = Identity("iss", "user", "catalog", frozenset({"catalog:read"}))
    page = await reader.read_operation(owner, spec.operation_id, arguments(spec))
    assert page.catalog_projection
    assert [f.value for f in page.fields] == ["001", "SSD"]
    assert not page.truncated
    reader.contracts = {}
    with pytest.raises(CatalogError, match="capability_not_verified"):
        await reader.read_operation(owner, spec.operation_id, arguments(spec))


async def test_binary_projection_fails_closed_without_linux_limits(tmp_path, monkeypatch):
    monkeypatch.setattr("sys.platform", "darwin")
    owner = Identity("iss", "user", "catalog", frozenset({"catalog:read"}))
    name = "ed_public.getProductListDownloadXMLWithTransform"
    spec = next(s for s in READS if s.operation_id == name)
    reader = make_reader(lambda _: pytest.fail("unexpected request"), spec, tmp_path)
    args = arguments(spec) | {"transformation": "EDLINKXLS", "fileFormat": "XLS"}
    with pytest.raises(CatalogError, match="catalog_projection_unavailable"):
        await reader.read_operation(owner, name, args)


@pytest.mark.parametrize(
    "body,allowed",
    [
        (b"<Result><StoItem><SPresentTree/></StoItem></Result>", True),
        (b"<Result><StoItem Code='X'/></Result>", False),
        (b"<Result><StoItem><Unknown/></StoItem></Result>", False),
        (b"<Result>customer</Result>", False),
    ],
)
async def test_empty_hog_only(tmp_path, body, allowed):
    owner = Identity("iss", "user", "catalog", frozenset({"catalog:read"}))
    spec = next(s for s in READS if s.operation_id == "mega.X-HOG.targeted")
    reader = make_reader(lambda _: httpx.Response(200, content=body), spec, tmp_path)
    if allowed:
        page = await reader.read_operation(owner, spec.operation_id, arguments(spec))
        assert page.catalog_projection and page.fields == []
    else:
        with pytest.raises(CatalogError, match="catalog_projection_unavailable"):
            await reader.read_operation(owner, spec.operation_id, arguments(spec))


def test_ed_end_date_defaults_to_today_in_prague():
    from suppliermcp.suppliers.reads import validate_arguments

    spec = next(s for s in READS if s.operation_id == "ed_public.getInvoiceList")
    now = datetime(2026, 11, 5, 23, 30, tzinfo=UTC)
    assert validate_arguments(spec, {"dateFrom": "2026-11-01"}, now)["dateTo"] == "2026-11-06"


async def test_continuations_need_independent_operator_key_and_original_credentials(tmp_path):
    import base64
    import secrets

    from pydantic import SecretStr, ValidationError

    spec = next(s for s in READS if s.operation_id == "mega.StoItemBase.targeted")
    with pytest.raises(ValidationError, match="at least 32 bytes") as error:
        Settings(read_cursor_key="short-secret")
    assert "short-secret" not in str(error.value)
    supplier = make_reader(
        lambda _: httpx.Response(
            200, content=b"<Result><Item>" + b"x" * 3000 + b"</Item></Result>"
        ),
        spec,
        tmp_path,
    )
    key = SecretStr(base64.b64encode(secrets.token_bytes(32)).decode())

    def replica(signing, credentials=None):
        settings = supplier.settings.model_copy(
            update={"read_cursor_key": signing, "max_response_bytes": 1000}
        )
        if credentials:
            settings.credentials = credentials
        reader = OperationReader(settings, transport_factory=supplier.factory, clock=supplier.clock)
        reader.contracts = supplier.contracts
        return reader

    page = await replica(key).read_operation(IDENTITY, spec.operation_id, arguments(spec))
    cursor = page.next_cursor
    assert (
        cursor
        and (
            await replica(key).read_operation(
                IDENTITY, spec.operation_id, arguments(spec), cursor=cursor
            )
        ).fields
    )
    for other in (
        replica(None),
        replica(key, {"mega": (SecretStr("login"), SecretStr("rotated-password"))}),
    ):
        with pytest.raises(CatalogError, match="invalid_cursor"):
            await other.read_operation(IDENTITY, spec.operation_id, arguments(spec), cursor=cursor)


async def test_other_reviewed_elinkx_service_reuses_wrapped_reads(monkeypatch, tmp_path):
    import json
    from dataclasses import replace
    from xml.etree.ElementTree import fromstring

    from suppliermcp.suppliers import registry

    profile = replace(
        registry.SERVICES["ed_public"],
        supplier="fixture",
        account="fixture_account",
        host="fixture.example",
    )
    monkeypatch.setattr(registry, "SERVICES", {"fixture_service": profile})
    (tmp_path / "operation_contracts.json").write_text(
        json.dumps(
            {
                "fixture_service": {
                    "namespace": "urn:fixture",
                    "operations": {
                        "GetItem": ["read", "documents:read", [], "Item", "fixture WSDL"]
                    },
                }
            }
        )
    )
    monkeypatch.setattr(registry, "files", lambda _: tmp_path)
    monkeypatch.setattr(registry, "_registry", registry._registry.__wrapped__)
    spec = registry.resolve_operation("fixture_service.GetItem")

    def response(request):
        assert request.headers["host"] == "fixture.example"
        assert request.url.path == "/service.asmx"
        assert request.headers["soapaction"] == '"urn:fixture/GetItem"'
        assert "authorization" not in request.headers
        operation = fromstring(request.content).find(f"{{{SOAP}}}Body/{{urn:fixture}}GetItem")
        assert operation.findtext("{urn:fixture}login") == "fixture-login"
        return httpx.Response(
            200,
            content=f'<s:Envelope xmlns:s="{SOAP}"><s:Body>'
            '<GetItemResponse xmlns="urn:fixture"><GetItemResult>ok</GetItemResult>'
            "</GetItemResponse></s:Body></s:Envelope>".encode(),
        )

    reader = make_reader(response, spec, tmp_path)
    reader.settings = Settings(
        credentials={"fixture_account": ("fixture-login", "fixture-password")}
    )
    result = await reader.read_operation(IDENTITY, spec.operation_id, {})
    assert [field.value for field in result.fields] == ["ok"]
    assert account_binding("login", profile) != account_binding("login")
