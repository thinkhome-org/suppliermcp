from pathlib import Path

import httpx
import pytest

from suppliermcp.catalog.contracts import BatchManifest, CatalogError, SourceItem
from suppliermcp.suppliers.ed.gateway import EdGateway
from suppliermcp.suppliers.ed.public import EdPublicAdapter
from suppliermcp.suppliers.transport import SupplierTransport
from suppliermcp.sync.artifacts import ArtifactStore

PRODUCT = b"<ArrayOfProduct><Product><ProId>7</ProId><Code>0007</Code><Name>Memory</Name></Product></ArrayOfProduct>"


def test_ed_lowercase_export_status(tmp_path):
    def respond(request):
        if request.method == "POST":
            return httpx.Response(
                200,
                content=b"<Response><Status><StatusCode>DONE</StatusCode></Status><ProductListStatus><url>https://api.example/catalog</url><fileName>catalog.xml</fileName><isReady>true</isReady></ProductListStatus></Response>",
            )
        return httpx.Response(200, content=PRODUCT)

    transport = SupplierTransport(
        {"api.example"},
        {"getProductListDownloadXML", "getProductListDownloadZIP", "download"},
        client=httpx.Client(transport=httpx.MockTransport(respond)),
        resolver=lambda _: ["93.184.216.34"],
    )
    adapter = EdPublicAdapter(
        EdGateway(transport, "https://api.example/service", "test", "test"),
        ArtifactStore(tmp_path),
        transport,
    )
    manifest = adapter.fetch("catalog")
    assert Path(manifest.path).read_bytes() == PRODUCT
    assert [r.sku for r in adapter.parse(manifest) if isinstance(r, SourceItem)] == ["0007"]


def test_ed_not_ready_is_polled(tmp_path):
    class Gateway:
        calls = 0

        def call(self, method, **params):
            self.calls += 1
            return b"<Response><isReady>false</isReady></Response>" if self.calls == 1 else PRODUCT

    gateway = Gateway()
    adapter = EdPublicAdapter(gateway, ArtifactStore(tmp_path), sleep=lambda _: None)
    manifest = adapter.fetch("catalog")
    assert [r.sku for r in adapter.parse(manifest) if isinstance(r, SourceItem)] == ["0007"]


def test_ed_status_without_catalog_is_rejected(tmp_path):
    path = tmp_path / "status.xml"
    path.write_text("<Response><StatusCode>DONE</StatusCode></Response>")
    with pytest.raises(CatalogError, match="invalid_export"):
        list(
            EdPublicAdapter().parse(
                BatchManifest(interface="ed_public", domain="catalog", path=str(path))
            )
        )


class Chunks(httpx.SyncByteStream):
    def __init__(self, fail=False):
        self.fail = fail

    def __iter__(self):
        yield b"abc"
        if self.fail:
            raise httpx.ReadError("sensitive upstream message")
        yield b"def"


def test_partial_download_is_not_retained_as_complete(tmp_path):
    attempts = []

    def respond(request):
        attempts.append(1)
        return httpx.Response(200, stream=Chunks(fail=len(attempts) == 1))

    transport = SupplierTransport(
        {"api.example"},
        {"download"},
        client=httpx.Client(transport=httpx.MockTransport(respond)),
        resolver=lambda _: ["93.184.216.34"],
        sleep=lambda _: None,
    )
    manifest = BatchManifest(interface="ed_public", domain="catalog")
    path = transport.download("https://api.example/catalog", ArtifactStore(tmp_path), manifest)
    assert path.read_bytes() == b"abcdef"
    assert len(list(tmp_path.glob("*.data"))) == 1
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_streaming_limit_rejects_last_chunk(tmp_path):
    transport = SupplierTransport(
        {"api.example"},
        {"download"},
        client=httpx.Client(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, stream=Chunks()))
        ),
        resolver=lambda _: ["93.184.216.34"],
        max_bytes=5,
    )
    with pytest.raises(CatalogError, match="payload_too_large"):
        transport.download(
            "https://api.example/catalog",
            ArtifactStore(tmp_path),
            BatchManifest(interface="ed_public", domain="catalog"),
        )
    assert not list(tmp_path.glob("*.data"))
    assert not list(tmp_path.glob("*.json"))
