"""Stateless supplier reads with bounded concurrency and bounded result previews."""

import base64
import binascii
import hashlib
import hmac
import json
import logging
import re
import struct
import tempfile
import zipfile
from contextvars import ContextVar
from datetime import date, datetime
from functools import cache
from importlib.resources import files
from urllib.parse import urlencode
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.parsers import expat
from zoneinfo import ZoneInfo

import anyio
import httpx
from anyio.lowlevel import RunVar

from suppliermcp.access import Identity, require_scope
from suppliermcp.catalog.contracts import CatalogError, Model, utcnow
from suppliermcp.config import Settings
from suppliermcp.suppliers.catalog_projection import catalog_projection
from suppliermcp.suppliers.mega.capabilities import require_window, verified_export_window
from suppliermcp.suppliers.registry import OperationSpec, resolve_operation
from suppliermcp.suppliers.transport import SupplierTransport

_read_limiter = RunVar("supplier_read_capacity")
SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
_private_request = ContextVar("supplier_request", default=False)
# httpx logs full download URLs. These may act as bearer credentials.
for _logger in ("httpx", "httpcore.connection", "httpcore.http11", "httpcore.http2"):
    logging.getLogger(_logger).addFilter(lambda _: not _private_request.get())


class SupplierField(Model):
    path: str
    value: str
    offset: int = 0


class ReadResult(Model):
    operation_id: str
    output_schema: str
    fields: list[SupplierField]
    truncated: bool
    stable_pagination: bool = False
    next_cursor: str | None = None
    catalog_projection: bool = False


@cache
def _navigator_types():
    return json.loads(files(__package__).joinpath("navigator_schema.json").read_text())


def _argument(kind, value):
    if kind in _navigator_types():
        schema = _navigator_types()[kind]
        if not isinstance(value, dict) or value.keys() - {name for name, *_ in schema}:
            raise ValueError
        result = {}
        for name, typ, many, required in schema:
            if name not in value:
                if required:
                    raise ValueError
                continue
            values = value[name] if many else [value[name]]
            if not isinstance(values, list) or len(values) > 100:
                raise ValueError
            result[name] = [_argument(typ, item) for item in values]
        return result
    if kind == "boolean" and type(value) is bool:
        return str(value).lower()
    if kind in ("short", "int") and type(value) is int:
        bits = 16 if kind == "short" else 32
        if -(2 ** (bits - 1)) <= value < 2 ** (bits - 1):
            return str(value)
    if kind == "dateTime" and isinstance(value, str):
        if datetime.fromisoformat(value).tzinfo and "T" in value:
            return value
    if kind == "string" and isinstance(value, str) and len(value) <= 8000:
        if not re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]", value):
            return value
    raise ValueError


def validate_arguments(spec, arguments, now):
    try:
        if not isinstance(arguments, dict) or arguments.keys() - {f.name for f in spec.inputs}:
            raise ValueError
        if len(json.dumps(arguments, allow_nan=False)) > 32 * 1024:
            raise ValueError
        result = {}
        for field in spec.inputs:
            required = field.required or field.name.endswith("Symbol")
            if field.name in arguments:
                result[field.name] = _argument(field.xsd_type, arguments[field.name])
                if required and result[field.name] == "":
                    raise ValueError
            elif required:
                raise ValueError
        if "dateFrom" in result:
            result.setdefault(
                "dateTo", now.astimezone(ZoneInfo("Europe/Prague")).date().isoformat()
            )
            span = date.fromisoformat(result["dateTo"]) - date.fromisoformat(result["dateFrom"])
            if not 0 <= span.days < 31:
                raise ValueError
        if "Comodities" in {f.name for f in spec.inputs} and result.get("onStock") == "false":
            if not any(
                result.get(k, "").strip()
                for k in ("Comodities", "ComoditiesTree", "Producers", "Categories")
            ):
                raise ValueError
        if spec.mode == "delta" and datetime.fromisoformat(
            result["from"]
        ) >= datetime.fromisoformat(result["to"]):
            raise ValueError
        if "WithTransform" in spec.name:
            if spec.name.startswith("getInvoice"):
                if result.get("transformation") not in {"INVOICEOLD", "ISDOC_5", "ISDOC_6"}:
                    raise ValueError
            else:
                formats = {"EDLINKOLDXML": "XML", "EDLINKOLDCSV": "CSV", "EDLINKXLS": "XLS"}
                if (
                    result.get("transformation") not in formats
                    or result.get("fileFormat") != formats[result["transformation"]]
                ):
                    raise ValueError
        return result
    except (ValueError, TypeError, RecursionError):
        raise CatalogError("invalid_arguments") from None


def _append(parent, name, value):
    child = SubElement(parent, name)
    if isinstance(value, dict):
        for key, values in value.items():
            for item in values:
                _append(child, key, item)
    else:
        child.text = value


def _soap(spec, args, credentials):
    envelope = Element("soap:Envelope", {"xmlns:soap": SOAP})
    body = SubElement(envelope, "soap:Body")
    namespace = spec.action.removesuffix(spec.name)
    if spec.interface.startswith("ed_"):
        parent = SubElement(body, spec.name, {"xmlns": namespace.rstrip("/")})
        args = {"login": credentials[0], "password": credentials[1], **args}
    else:
        # Order.asmx uses bare document/literal message parts.
        parent = body
        parent.set("xmlns", namespace)
    for name, value in args.items():
        _append(parent, name, value)
    return tostring(envelope, encoding="utf-8")


class _Page:
    # Two counters, a content digest and an authentication tag, without document data.
    cursor_format = struct.Struct(">QQ32s")
    cursor_length = 108

    def __init__(self, spec, limit, identity, arguments, credentials, cursor, now, ttl):
        self.result = ReadResult(
            operation_id=spec.operation_id,
            output_schema=spec.output_schema,
            fields=[],
            truncated=False,
            catalog_projection=spec.scope == "catalog:read"
            and "documents:read" not in identity.scopes,
        )
        context = json.dumps(
            [
                "suppliermcp/read-page/v1",
                identity.principal,
                self.result.catalog_projection,
                spec.operation_id,
                arguments,
                limit,
            ],
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        key = json.dumps(credentials, separators=(",", ":")).encode()
        self.key = hmac.digest(key, context, "sha256")
        self.start, self.expected, self.expires = 0, None, now + ttl
        if cursor is not None:
            try:
                if not isinstance(cursor, str) or len(cursor) != self.cursor_length:
                    raise ValueError
                token = base64.b64decode(cursor, altchars=b"-_", validate=True)
                payload, tag = token[:-32], token[-32:]
                if not hmac.compare_digest(tag, hmac.digest(self.key, payload, "sha256")):
                    raise ValueError
                self.start, self.expires, self.expected = self.cursor_format.unpack(payload)
                if self.expires <= now:
                    raise ValueError
            except (ValueError, binascii.Error, struct.error):
                raise CatalogError("invalid_cursor") from None
        self.digest = hashlib.sha256()
        self.ordinal = 0
        self.left = limit - len(self.result.model_dump_json().encode()) - self.cursor_length
        self.chunk_chars = max(1, min(4096, (self.left - 128) // 8))

    def field(self, path, value, offset=0):
        for at in range(0, max(1, len(value)), self.chunk_chars):
            item = SupplierField(
                path=path, value=value[at : at + self.chunk_chars], offset=offset + at
            )
            encoded = item.model_dump_json().encode()
            self.digest.update(encoded + b"\n")
            self.ordinal += 1
            if self.ordinal <= self.start or self.result.truncated:
                continue
            cost = len(encoded) + 1
            if self.left < cost:
                if not self.result.fields:
                    raise CatalogError("response_too_large")
                self.result.truncated = True
            else:
                self.left -= cost
                self.result.fields.append(item)

    def finish(self):
        digest = self.digest.digest()
        if self.expected is not None and self.expected != digest:
            raise CatalogError("source_snapshot_changed")
        if self.result.truncated:
            offset = self.start + len(self.result.fields)
            payload = self.cursor_format.pack(offset, self.expires, digest)
            self.result.next_cursor = base64.urlsafe_b64encode(
                payload + hmac.digest(self.key, payload, "sha256")
            ).decode()
        return self.result


def _xml(chunks, spec, preview, *, soap=False, export=False, prefix=""):
    parser = expat.ParserCreate(namespace_separator=" ")
    stack = []
    download = None
    result_seen = False
    body_seen = False

    def invalid(*_):
        raise CatalogError("invalid_supplier_xml")

    def start(tag, attrs):
        nonlocal result_seen, body_seen
        ns, _, name = tag.rpartition(" ")
        if len(stack) >= 64 or len(name) > 256:
            invalid()
        if name in ("Fault", "Error") and (not stack or name == "Fault" or export):
            raise CatalogError("supplier_response_error")
        if soap:
            expected = [(SOAP, "Envelope"), (SOAP, "Body")]
            operation_ns = spec.action.removesuffix(spec.name)
            if spec.interface.startswith("ed_"):
                operation_ns = operation_ns.rstrip("/")
                expected.append((operation_ns, spec.name + "Response"))
            expected.append((operation_ns, spec.name + "Result"))
            if len(stack) < len(expected) and (ns, name) != expected[len(stack)]:
                invalid()
            if len(stack) == 1:
                body_seen = True
            if len(stack) == len(expected) - 1:
                result_seen = True
        if export and not stack and name not in {"Result", "SHOP"}:
            invalid()
        if stack:
            stack[-1]["text"] = ""
            stack[-1]["children"] += 1
        index = stack[-1]["children"] if stack else 1
        hidden = (stack and stack[-1]["hidden"]) or (
            (
                spec.scope == "catalog:read"
                and name.lower() in {"addressid", "address", "customeraddress"}
            )
            or name.lower() in {"password", "login", "errortext"}
        )
        project = preview.result.catalog_projection and not (soap and spec.strategy == "download")
        node = None
        if project:
            qualified = f"{{{ns}}}{name}" if ns else name
            if not stack:
                node = catalog_projection(spec.interface, spec.name, qualified)
            elif stack[-1]["node"] is not None:
                node = stack[-1]["node"].child(qualified)
        frame = dict(
            name=name,
            children=0,
            text="",
            offset=0,
            hidden=hidden,
            index=index,
            node=node,
            allow_text=not project or (node is not None and node.text),
        )

        stack.append(frame)
        if not hidden and (spec.strategy != "download" or not soap):
            for attr, value in attrs.items():
                if project and (node is None or not node.allows_attribute(attr)):
                    continue
                attr = attr.rsplit(" ", 1)[-1]
                if attr.lower() not in {"login", "password"} and not (
                    spec.scope == "catalog:read" and attr.lower() == "addressid"
                ):
                    preview.field(path() + "/@" + attr, value)

    def path():
        return prefix + "/".join(f"{s['name']}[{s['index']}]" for s in stack)

    def chars(value):
        if not stack:
            return
        f = stack[-1]
        control = f["name"].lower() == "statuscode" or (
            soap and spec.strategy == "download" and f["name"].lower() in {"url", "isready"}
        )
        if control:
            if len(f["text"]) + len(value) > 8192:
                invalid()
            f["text"] += value
        elif (
            f["allow_text"]
            and not f["hidden"]
            and not f["children"]
            and not (soap and spec.strategy == "download")
        ):
            text = f["text"] + value
            while len(text) > preview.chunk_chars:
                preview.field(path(), text[: preview.chunk_chars], f["offset"])
                f["offset"] += preview.chunk_chars
                text = text[preview.chunk_chars :]
            f["text"] = text

    def end(_):
        nonlocal download
        f = stack[-1]
        name, value = f["name"].lower(), f["text"]
        if name == "statuscode" and value.strip().upper() == "ERROR":
            raise CatalogError("supplier_response_error")
        if soap and spec.strategy == "download":
            if name == "url":
                if download:
                    invalid()
                download = value.strip()
            if name == "isready" and value.strip().lower() not in {"true", "1"}:
                raise CatalogError("export_not_ready", retryable=True)
        elif (
            f["allow_text"]
            and not f["hidden"]
            and not f["children"]
            and (f["offset"] or value.strip())
        ):
            if value:
                preview.field(path(), value, f["offset"])
        stack.pop()

    parser.StartDoctypeDeclHandler = invalid
    parser.StartElementHandler, parser.CharacterDataHandler, parser.EndElementHandler = (
        start,
        chars,
        end,
    )
    try:
        for chunk in chunks:
            parser.Parse(chunk, False)
        parser.Parse(b"", True)
    except (expat.ExpatError, LookupError):
        raise CatalogError("invalid_supplier_xml") from None
    if soap and not result_seen and not (body_seen and spec.interface == "mega_order"):
        invalid()
    return download


class OperationReader:
    def __init__(self, settings: Settings, *, transport_factory=SupplierTransport, clock=utcnow):
        self.settings, self.factory, self.clock = settings, transport_factory, clock
        self.contracts = (
            json.loads(settings.source_contracts_path.read_text())
            if settings.source_contracts_path
            else {}
        )

    async def read_operation(
        self, identity: Identity, operation_id: str, arguments: dict, *, cursor: str | None = None
    ) -> ReadResult:
        spec = resolve_operation(operation_id)
        require_scope(identity, spec.scope)
        args = validate_arguments(spec, arguments, self.clock())
        limiter = _read_limiter.get(None)
        if limiter is None:
            limiter = anyio.CapacityLimiter(4)
            _read_limiter.set(limiter)
        return await anyio.to_thread.run_sync(
            self._read, spec, args, identity, cursor, limiter=limiter
        )

    def _read(self, spec: OperationSpec, args, identity, cursor):
        interface = "mega" if spec.interface.startswith("mega") else spec.interface
        credentials = self.settings.credentials.get(interface)
        if not credentials:
            raise CatalogError("source_not_configured")
        credentials = tuple(v.get_secret_value() for v in credentials)

        def window():
            if spec.interface == "mega":
                contract = self.contracts.get("mega", {}).get("exports", {}).get(spec.name, {})
                require_window(verified_export_window(spec, contract), spec.mode, self.clock())

        preview = _Page(
            spec,
            self.settings.max_response_bytes,
            identity,
            args,
            credentials,
            cursor,
            int(self.clock().timestamp()),
            self.settings.result_ttl_seconds,
        )
        if preview.result.catalog_projection:
            if spec.interface == "mega":
                catalog_projection(
                    "mega",
                    spec.name,
                    "SHOP" if spec.name in {"StoItemShop_El", "StoItemShoptet_El"} else "Result",
                )
            elif args.get("fileFormat", "XML") != "XML":
                raise CatalogError("catalog_projection_unavailable")
        window()
        hosts = {
            httpx.URL(spec.target).host,
            *self.contracts.get(interface, {}).get("download_hosts", []),
        }
        transport = self.factory(
            hosts,
            {spec.operation_id, "download"},
            auth=credentials if interface == "mega" else None,
            max_bytes=self.settings.max_download_bytes,
        )
        token = _private_request.set(True)
        try:
            params = {
                "endpoint": spec.operation_id,
                "before_request": window,
                "timeout": httpx.Timeout(self.settings.download_timeout_seconds, connect=10),
            }
            if spec.interface == "mega":
                transport.consume(
                    "POST",
                    spec.target,
                    body=urlencode({"resultType": spec.name, **args}).encode(),
                    content_type="application/x-www-form-urlencoded",
                    consume=lambda chunks: _xml(chunks, spec, preview, export=True),
                    **params,
                )
            else:
                url = transport.consume(
                    "POST",
                    spec.target,
                    body=_soap(spec, args, credentials),
                    soap_action=f'"{spec.action}"',
                    consume=lambda chunks: _xml(chunks, spec, preview, soap=True),
                    **params,
                )
                if spec.strategy == "download":
                    if not url:
                        raise CatalogError("missing_download_url")
                    transport.consume(
                        "GET",
                        url,
                        endpoint="download",
                        timeout=params["timeout"],
                        consume=lambda chunks: self._download(chunks, spec, preview, args),
                    )
            return preview.finish()
        finally:
            transport.client.close()
            _private_request.reset(token)

    def _download(self, chunks, spec, preview, args):
        def consume(data, prefix=""):
            if args.get("fileFormat", "XML").upper() == "XML":
                _xml(data, spec, preview, prefix=prefix)
            else:
                # Fixed-size independently decodable blocks preserve non-XML formats.
                for i, chunk in enumerate(data):
                    preview.field(f"{prefix}base64[{i + 1}]", base64.b64encode(chunk).decode())

        expanded = 0

        def bounded(data):
            nonlocal expanded
            for chunk in data:
                expanded += len(chunk)
                if expanded > self.settings.max_expanded_bytes:
                    raise CatalogError("payload_too_large")
                yield chunk

        if "ZIP" not in spec.name:
            consume(bounded(chunks))
            return
        with tempfile.SpooledTemporaryFile(max_size=1024**2) as buffer:
            for chunk in chunks:
                buffer.write(chunk)
            try:
                with zipfile.ZipFile(buffer) as archive:
                    entries = archive.infolist()
                    if (
                        len(entries) > 100
                        or sum(e.file_size for e in entries) > self.settings.max_expanded_bytes
                    ):
                        raise CatalogError("payload_too_large")
                    for index, entry in enumerate(entries, 1):
                        if not entry.is_dir():
                            with archive.open(entry) as f:
                                consume(
                                    bounded(iter(lambda: f.read(65536), b"")), f"member[{index}]/"
                                )
            except (zipfile.BadZipFile, RuntimeError, NotImplementedError):
                raise CatalogError("invalid_supplier_archive") from None
