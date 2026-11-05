import httpx
import pytest
from suppliermcp.suppliers.transport import SupplierTransport
from suppliermcp.catalog.contracts import CatalogError


def transport(handler, resolver=lambda h: ['93.184.216.34'], **kw):
    return SupplierTransport({'api.example'}, {'read'}, client=httpx.Client(transport=httpx.MockTransport(handler)), resolver=resolver, sleep=lambda _: None, **kw)


def test_dns_rebinding():
    seen = []
    def handler(request):
        seen.append((request.url.host, request.headers['host'], request.extensions['sni_hostname']))
        return httpx.Response(200, content=b'<Result/>')
    assert transport(handler).read('GET', 'https://api.example/', endpoint='read') == b'<Result/>'
    assert seen == [('93.184.216.34', 'api.example', 'api.example')]


@pytest.mark.parametrize('ip', ['127.0.0.1', '::1', '10.0.0.1', '169.254.169.254'])
def test_private_destinations_rejected(ip):
    t = transport(lambda r: httpx.Response(200), resolver=lambda h: [ip])
    with pytest.raises(CatalogError, match='unsafe_download'):
        t.read('GET', 'https://api.example/', endpoint='read')


def test_redirect_checks_every_hop():
    t = transport(lambda r: httpx.Response(302, headers={'Location': 'https://127.0.0.1/secret'}))
    with pytest.raises(CatalogError, match='unsafe_download'):
        t.read('GET', 'https://api.example/', endpoint='read')


def test_retry_budget_and_redaction():
    calls = []
    def failure(request):
        calls.append(request)
        raise httpx.ConnectError('secret password in upstream error')
    with pytest.raises(CatalogError) as exc:
        transport(failure).read('GET', 'https://api.example/?token=secret', endpoint='read')
    assert len(calls) == 3
    assert 'secret' not in str(exc.value.as_dict())


def test_rejects_write_and_limits_response():
    t = transport(lambda r: httpx.Response(200, content=b'abcdef'), max_bytes=5)
    with pytest.raises(CatalogError, match='operation_not_allowed'):
        t.read('POST', 'https://api.example/', endpoint='createOrder')
    with pytest.raises(CatalogError, match='payload_too_large'):
        t.read('GET', 'https://api.example/', endpoint='read')
