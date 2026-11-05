import io
import zipfile
from datetime import timedelta
import pytest
from suppliermcp.catalog.contracts import BatchManifest, CatalogError, utcnow
from suppliermcp.sync.artifacts import ArtifactStore, parse_xml


def manifest():
    return BatchManifest(interface='mega', domain='catalog')


def test_rejects_entity_and_archive_escape(tmp_path):
    p = tmp_path / 'bad.xml'
    p.write_bytes(b'<!DOCTYPE a [<!ENTITY x SYSTEM "file:///etc/passwd">]><a>&x;</a>')
    with pytest.raises(CatalogError):
        list(parse_xml(p))
    z = io.BytesIO()
    with zipfile.ZipFile(z, 'w') as f:
        f.writestr('../escape.xml', '<Result/>')
    p.write_bytes(z.getvalue())
    with pytest.raises(CatalogError):
        list(parse_xml(p))


def test_parse_and_expansion_limit(tmp_path):
    p = tmp_path / 'data'
    p.write_text('<Result><StoItem Code="0001"/></Result>')
    assert [e.attrib['Code'] for e in parse_xml(p) if e.tag == 'StoItem'] == ['0001']
    with pytest.raises(CatalogError):
        list(parse_xml(p, max_expanded=10))


def test_retention_protects_active_and_latest(tmp_path):
    store = ArtifactStore(tmp_path, budget=50)
    m = manifest()
    newest = store.save([b'latest'], m)
    store.mark(newest, 'success', m)
    active = store.save([b'active'], manifest())
    store.mark(active, 'active', manifest())
    old = store.save([b'failed'], manifest())
    store.mark(old, 'failed', manifest(), now=utcnow()-timedelta(days=8))
    assert old in store.prune(utcnow())
    assert newest.exists() and active.exists()
    with pytest.raises(CatalogError, match='artifact_budget_exceeded'):
        store.save([b'x'*100], manifest())
    assert newest.exists() and active.exists()
