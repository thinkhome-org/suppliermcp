import io
import zipfile
from datetime import UTC, datetime

import httpx
import pytest

from suppliermcp.access import Identity
from suppliermcp.catalog.contracts import CatalogError
from suppliermcp.config import Settings
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

        now = datetime(2026, 11, 2 + spec.days[0], spec.hours[0], tzinfo=ZoneInfo("Europe/Prague"))
    return OperationReader(settings, transport_factory=factory, clock=lambda: now)


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
