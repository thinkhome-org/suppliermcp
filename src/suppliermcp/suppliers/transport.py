"""Read-only HTTPS transport with pinned public destinations and safe failures."""

import ipaddress
import logging
import socket
import time
from contextlib import contextmanager
from contextvars import ContextVar
from urllib.parse import urljoin
from xml.etree.ElementTree import ParseError

import httpx
from defusedxml.common import DefusedXmlException
from defusedxml.ElementTree import fromstring

from suppliermcp.catalog.contracts import CatalogError


_private_request = ContextVar("supplier_request", default=False)
# httpx logs full download URLs. These may act as bearer credentials.
for _logger in ("httpx", "httpcore.connection", "httpcore.http11", "httpcore.http2"):
    logging.getLogger(_logger).addFilter(lambda _: not _private_request.get())


@contextmanager
def _suppress_supplier_http_logs():
    token = _private_request.set(True)
    try:
        yield
    finally:
        _private_request.reset(token)


def resolve(host):
    return list(
        dict.fromkeys(x[4][0] for x in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM))
    )


def _soap_fault(response):
    if response.headers.get("content-encoding", "identity").lower() != "identity":
        return None
    data = bytearray()
    for chunk in response.iter_bytes(chunk_size=4096):
        if len(data) + len(chunk) > 64 * 1024:
            return None
        data.extend(chunk)
    try:
        root = fromstring(data, forbid_dtd=True)
    except (ParseError, DefusedXmlException, ValueError, LookupError):
        return None
    namespace = "{http://schemas.xmlsoap.org/soap/envelope/}"
    if root.tag != namespace + "Envelope":
        return None
    fault = root.find(namespace + "Body/" + namespace + "Fault")
    if fault is None:
        return None
    code = (fault.findtext("faultcode") or "").rsplit(":", 1)[-1]
    if code in ("Client", "Sender"):
        return CatalogError("supplier_soap_client_fault")
    if code not in ("Server", "Receiver"):
        return CatalogError("supplier_soap_fault")
    detail = (fault.findtext("faultstring") or "").casefold()
    for signature, label in (
        ("sqlexception", "sql"),
        ("applicationexception", "application"),
        ("nullreferenceexception", "null_reference"),
    ):
        if signature in detail:
            return CatalogError("supplier_soap_server_" + label + "_fault")
    return CatalogError("supplier_soap_server_fault")


class SupplierTransport:
    def __init__(
        self,
        hosts,
        operations,
        *,
        client=None,
        resolver=resolve,
        sleep=time.sleep,
        max_bytes=256 * 1024**2,
        download_timeout=300,
        auth=None,
    ):
        self.hosts, self.operations = set(hosts), set(operations)
        self.download_timeout = download_timeout
        self.client = client or httpx.Client(timeout=30, trust_env=False)
        self.resolver, self.sleep, self.max_bytes, self.auth = resolver, sleep, max_bytes, auth

    def read(self, method, url, *, endpoint, body=None, soap_action=None) -> bytes:
        return self._request(
            method,
            url,
            endpoint=endpoint,
            body=body,
            soap_action=soap_action,
            consume=lambda chunks: b"".join(chunks),
        )

    def consume(self, method, url, *, endpoint, consume, **options):
        """Consume a bounded response while its pinned connection is open."""
        return self._request(
            method, url, endpoint=endpoint, consume=consume, restartable=False, **options
        )

    def download(self, url, store, manifest, *, endpoint="download", before_request=None):
        return self._request(
            "GET",
            url,
            endpoint=endpoint,
            consume=lambda chunks: store.save(chunks, manifest),
            before_request=before_request,
            timeout=httpx.Timeout(self.download_timeout, connect=10),
        )

    @_suppress_supplier_http_logs()
    def _request(
        self,
        method: str,
        url: str,
        *,
        endpoint: str,
        consume,
        body: bytes | None = None,
        soap_action: str | None = None,
        before_request=None,
        content_type="text/xml; charset=utf-8",
        restartable=True,
        timeout=httpx.USE_CLIENT_DEFAULT,
    ):
        if endpoint not in self.operations or method not in {"GET", "POST"}:
            raise CatalogError("operation_not_allowed")
        try:
            original = httpx.URL(url)
        except (httpx.InvalidURL, ValueError):
            raise CatalogError("unsafe_download") from None
        for attempt in range(3):
            current = original
            try:
                for redirect in range(6):
                    if (
                        current.scheme != "https"
                        or current.host not in self.hosts
                        or current.userinfo
                        or current.port not in (None, 443)
                    ):
                        raise CatalogError("unsafe_download")
                    ips = self.resolver(current.host)
                    if not ips or any(not ipaddress.ip_address(ip).is_global for ip in ips):
                        raise CatalogError("unsafe_download")
                    # Connect to validated IP; retain original hostname for certificate verification.
                    pinned = current.copy_with(host=ips[0])
                    headers = {
                        "Host": current.host,
                        "Accept-Encoding": "identity",
                        "Connection": "close",
                    }
                    if body is not None:
                        headers["Content-Type"] = content_type
                    if soap_action:
                        headers["SOAPAction"] = soap_action
                    auth = self.auth if current == original else None
                    if before_request:
                        before_request()
                    with self.client.stream(
                        method,
                        pinned,
                        headers=headers,
                        content=body,
                        auth=auth,
                        extensions={"sni_hostname": current.host},
                        timeout=timeout,
                    ) as response:
                        if response.is_redirect:
                            if method != "GET" or redirect == 5:
                                raise CatalogError("unsafe_download")
                            current = httpx.URL(urljoin(str(current), response.headers["location"]))
                            continue
                        if response.status_code in (401, 403):
                            raise CatalogError("permission_denied")
                        if not restartable and soap_action and response.status_code >= 400:
                            fault = _soap_fault(response)
                            if fault is not None:
                                raise fault
                        if response.status_code == 429 or response.status_code >= 500:
                            if attempt < 2:
                                delay = response.headers.get("retry-after", "")
                                self.sleep(min(int(delay), 60) if delay.isdigit() else 2**attempt)
                                break
                            code = "supplier_unavailable"
                            if not restartable:
                                code = (
                                    "supplier_rate_limited"
                                    if response.status_code == 429
                                    else "supplier_http_5xx"
                                )
                            raise CatalogError(code, retryable=True)
                        if response.status_code != 200:
                            raise CatalogError("supplier_response_error")
                        if (
                            response.headers.get("content-encoding", "identity").lower()
                            != "identity"
                        ):
                            raise CatalogError("unsupported_content_encoding")

                        def chunks():
                            size = 0
                            for chunk in response.iter_bytes(chunk_size=64 * 1024):
                                size += len(chunk)
                                if size > self.max_bytes:
                                    raise CatalogError("payload_too_large")
                                yield chunk

                        # A streaming consumer may already have processed part of the response.
                        try:
                            return consume(chunks())
                        except httpx.TransportError as error:
                            if restartable:
                                raise
                            code = (
                                "supplier_timeout"
                                if isinstance(error, httpx.TimeoutException)
                                else "supplier_connection_error"
                            )
                            raise CatalogError(code, retryable=True) from None
            except httpx.InvalidURL:
                raise CatalogError("unsafe_download") from None
            except CatalogError:
                raise
            except (httpx.HTTPError, OSError, ValueError, KeyError) as error:
                if attempt == 2:
                    code = "supplier_unavailable"
                    if not restartable:
                        code = (
                            "supplier_timeout"
                            if isinstance(error, httpx.TimeoutException)
                            else "supplier_connection_error"
                        )
                    raise CatalogError(code, retryable=True) from None
                self.sleep(2**attempt)
        raise CatalogError("supplier_unavailable", retryable=True)
