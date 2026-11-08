import httpx
import pytest

from suppliermcp.catalog.contracts import CatalogError
from suppliermcp.suppliers.transport import SupplierTransport


def transport(handler, resolver=lambda h: ["93.184.216.34"], **kw):
    return SupplierTransport(
        {"api.example"},
        {"read"},
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        resolver=resolver,
        sleep=lambda _: None,
        **kw,
    )


def test_dns_rebinding():
    seen = []

    def handler(request):
        seen.append((request.url.host, request.headers["host"], request.extensions["sni_hostname"]))
        return httpx.Response(200, content=b"<Result/>")

    assert transport(handler).read("GET", "https://api.example/", endpoint="read") == b"<Result/>"
    assert seen == [("93.184.216.34", "api.example", "api.example")]


@pytest.mark.parametrize("ip", ["127.0.0.1", "::1", "10.0.0.1", "169.254.169.254"])
def test_private_destinations_rejected(ip):
    t = transport(lambda r: httpx.Response(200), resolver=lambda h: [ip])
    with pytest.raises(CatalogError, match="unsafe_download"):
        t.read("GET", "https://api.example/", endpoint="read")


def test_redirect_checks_every_hop():
    t = transport(lambda r: httpx.Response(302, headers={"Location": "https://127.0.0.1/secret"}))
    with pytest.raises(CatalogError, match="unsafe_download"):
        t.read("GET", "https://api.example/", endpoint="read")


def test_retry_budget_and_redaction():
    calls = []

    def failure(request):
        calls.append(request)
        raise httpx.ConnectError("secret password in upstream error")

    with pytest.raises(CatalogError) as exc:
        transport(failure).read("GET", "https://api.example/?token=secret", endpoint="read")
    assert len(calls) == 3
    assert "secret" not in str(exc.value.as_dict())


def test_rejects_write_and_limits_response():
    t = transport(lambda r: httpx.Response(200, content=b"abcdef"), max_bytes=5)
    with pytest.raises(CatalogError, match="operation_not_allowed"):
        t.read("POST", "https://api.example/", endpoint="createOrder")
    with pytest.raises(CatalogError, match="payload_too_large"):
        t.read("GET", "https://api.example/", endpoint="read")


def test_rejects_unexpected_http_compression():
    import gzip

    def handler(request):
        return httpx.Response(
            200, headers={"Content-Encoding": "gzip"}, content=gzip.compress(b"x" * 100000)
        )

    transport = SupplierTransport(
        {"example.com"},
        {"read"},
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        resolver=lambda host: ["8.8.8.8"],
    )
    with pytest.raises(CatalogError) as error:
        transport.read("GET", "https://example.com/export", endpoint="read")
    assert error.value.code == "unsupported_content_encoding"


@pytest.mark.parametrize(
    ("fault", "detail", "expected"),
    [
        ("Client", "private supplied arguments", "supplier_soap_client_fault"),
        (
            "Server",
            "System.Data.SqlClient.SqlException: private account row",
            "supplier_soap_server_sql_fault",
        ),
        (
            "Server",
            "System.ApplicationException: private account row",
            "supplier_soap_server_application_fault",
        ),
    ],
)
def test_soap_fault_is_sanitized_and_not_retried(fault, detail, expected):
    count = 0

    def reply(request):
        nonlocal count
        count += 1
        return httpx.Response(
            500,
            content=f'<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><s:Fault><faultcode>s:{fault}</faultcode><faultstring>{detail}</faultstring></s:Fault></s:Body></s:Envelope>'.encode(),
        )

    with pytest.raises(CatalogError) as error:
        transport(reply).consume(
            "POST",
            "https://api.example/read",
            endpoint="read",
            soap_action='"action"',
            consume=list,
        )
    assert error.value.code == expected and not error.value.retryable
    assert count == 1 and "private" not in str(error.value.as_dict())


def test_read_separates_http_service_errors_from_timeouts():
    for code in ("supplier_http_5xx", "supplier_timeout"):

        def fail(request, expected=code):
            if expected == "supplier_timeout":
                raise httpx.ReadTimeout("private content")
            return httpx.Response(503, content=b"private content")

        with pytest.raises(CatalogError) as error:
            transport(fail).consume(
                "GET", "https://api.example/read", endpoint="read", consume=list
            )
        assert error.value.code == code and error.value.retryable


def test_worker_request_keeps_signed_url_out_of_http_logs(caplog):
    caplog.set_level("INFO", logger="httpx")
    t = transport(lambda r: httpx.Response(200, content=b"catalog"))
    assert t.read("GET", "https://api.example/export?token=private-example", endpoint="read")
    assert "private-example" not in caplog.text
    t.client.get("https://api.example/public-test")
    assert "public-test" in caplog.text


def test_worker_download_bounds_stalled_reads_and_does_not_retry_shutdown():
    import threading

    from procrastinate.exceptions import JobAborted
    from procrastinate.job_context import JobContext

    from suppliermcp.sync.lifecycle import abortable_job

    aborted = threading.Event()
    context = JobContext(
        app=None, job=None, start_timestamp=0, abort_reason=lambda: aborted.is_set()
    )
    calls = []

    def handler(request):
        calls.append(request)
        assert request.extensions["timeout"]["read"] == 60
        aborted.set()
        raise httpx.ReadTimeout("fixture stalled read", request=request)

    class Store:
        def save(self, chunks, manifest):
            return b"".join(chunks)

    t = transport(handler, download_timeout=900)

    @abortable_job
    def job():
        t.download("https://api.example/file", Store(), None, endpoint="read")

    with pytest.raises(JobAborted):
        job(context)
    assert len(calls) == 1


def test_ordinary_download_preserves_configured_read_timeout():
    def handler(request):
        assert request.extensions["timeout"]["read"] == 900
        return httpx.Response(200, content=b"fixture")

    class Store:
        def save(self, chunks, manifest):
            return b"".join(chunks)

    assert (
        transport(handler, download_timeout=900).download(
            "https://api.example/file", Store(), None, endpoint="read"
        )
        == b"fixture"
    )


def test_worker_abort_is_checked_between_small_network_fragments():
    import threading

    from procrastinate.exceptions import JobAborted
    from procrastinate.job_context import JobContext

    from suppliermcp.sync.lifecycle import abortable_job

    aborted = threading.Event()
    context = JobContext(
        app=None, job=None, start_timestamp=0, abort_reason=lambda: aborted.is_set()
    )

    class Stream(httpx.SyncByteStream):
        def __iter__(self):
            yield b"a"
            aborted.set()
            yield b"b"
            pytest.fail("waited for a full buffered chunk after shutdown")

    t = transport(lambda request: httpx.Response(200, stream=Stream()))

    @abortable_job
    def job():
        return t.read("GET", "https://api.example/file", endpoint="read")

    with pytest.raises(JobAborted):
        job(context)
