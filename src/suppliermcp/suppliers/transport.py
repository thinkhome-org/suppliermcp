"""Read-only HTTPS transport with pinned public destinations and safe failures."""

import ipaddress
import socket
import time
from urllib.parse import urljoin

import httpx

from suppliermcp.catalog.contracts import CatalogError


def resolve(host):
    return list(
        dict.fromkeys(x[4][0] for x in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM))
    )


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
        auth=None,
    ):
        self.hosts, self.operations = set(hosts), set(operations)
        self.client = client or httpx.Client(timeout=30, trust_env=False)
        self.resolver, self.sleep, self.max_bytes, self.auth = resolver, sleep, max_bytes, auth

    def read(
        self,
        method: str,
        url: str,
        *,
        endpoint: str,
        body: bytes | None = None,
        soap_action: str | None = None,
    ) -> bytes:
        if endpoint not in self.operations or method not in {"GET", "POST"}:
            raise CatalogError("operation_not_allowed")
        original = httpx.URL(url)
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
                        headers["Content-Type"] = "text/xml; charset=utf-8"
                    if soap_action:
                        headers["SOAPAction"] = soap_action
                    auth = self.auth if current == original else None
                    with self.client.stream(
                        method,
                        pinned,
                        headers=headers,
                        content=body,
                        auth=auth,
                        extensions={"sni_hostname": current.host},
                    ) as response:
                        if response.is_redirect:
                            if method != "GET" or redirect == 5:
                                raise CatalogError("unsafe_download")
                            current = httpx.URL(urljoin(str(current), response.headers["location"]))
                            continue
                        if response.status_code in (401, 403):
                            raise CatalogError("permission_denied")
                        if response.status_code == 429 or response.status_code >= 500:
                            if attempt < 2:
                                delay = response.headers.get("retry-after", "")
                                self.sleep(min(int(delay), 60) if delay.isdigit() else 2**attempt)
                                break
                            raise CatalogError("supplier_unavailable", retryable=True)
                        if response.status_code != 200:
                            raise CatalogError("supplier_response_error")
                        if (
                            response.headers.get("content-encoding", "identity").lower()
                            != "identity"
                        ):
                            raise CatalogError("unsupported_content_encoding")
                        chunks, size = [], 0
                        for chunk in response.iter_bytes():
                            size += len(chunk)
                            if size > self.max_bytes:
                                raise CatalogError("payload_too_large")
                            chunks.append(chunk)
                        return b"".join(chunks)
            except CatalogError:
                raise
            except (httpx.HTTPError, OSError, ValueError, KeyError):
                if attempt == 2:
                    raise CatalogError("supplier_unavailable", retryable=True) from None
                self.sleep(2**attempt)
        raise CatalogError("supplier_unavailable", retryable=True)
