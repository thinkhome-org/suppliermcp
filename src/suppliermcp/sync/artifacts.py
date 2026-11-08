"""Bounded, content-addressed import evidence, never a public price history."""

import fcntl
import hashlib
import json
import os
import secrets
import tempfile
import zipfile
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path, PurePosixPath
from xml.etree.ElementTree import ParseError

from defusedxml.common import DefusedXmlException
from defusedxml.ElementTree import iterparse

from suppliermcp.catalog.contracts import CatalogError, utcnow
from suppliermcp.sync.lifecycle import check_abort


class ArtifactStore:
    def __init__(self, root: Path, budget=5 * 1024**3):
        self.root, self.budget = Path(root), budget
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)

    @contextmanager
    def lock(self):
        with (self.root / ".lock").open("a") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def save(self, stream, manifest):
        with self.lock():
            return self._save(stream, manifest)

    def _save(self, stream, manifest):
        self._prune(utcnow())
        used = sum(p.stat().st_size for p in self.root.glob("*.data"))
        digest, size = hashlib.sha256(), 0
        fd, name = tempfile.mkstemp(dir=self.root)
        try:
            with os.fdopen(fd, "wb") as f:
                for chunk in stream:
                    check_abort()
                    size += len(chunk)
                    if size + used > self.budget:
                        raise CatalogError("artifact_budget_exceeded")
                    f.write(chunk)
                    digest.update(chunk)
            target = self.root / (digest.hexdigest() + "_" + secrets.token_hex(8) + ".data")
            os.replace(name, target)
            manifest.path, manifest.artifact_sha256 = str(target), digest.hexdigest()
            self._mark(target, "active", manifest)
            return target
        finally:
            Path(name).unlink(missing_ok=True)

    def mark(self, path, state, manifest, now=None):
        with self.lock():
            self._mark(path, state, manifest, now)

    def _mark(self, path, state, manifest, now=None):
        meta = {
            "state": state,
            "time": (now or utcnow()).isoformat(),
            "interface": manifest.interface,
            "domain": manifest.domain,
            "endpoint": manifest.endpoint,
        }
        fd, name = tempfile.mkstemp(dir=self.root)
        with os.fdopen(fd, "w") as handle:
            json.dump(meta, handle)
        os.replace(name, Path(path).with_suffix(".json"))

    def prune(self, now):
        with self.lock():
            return self._prune(now)

    def _prune(self, now):
        from datetime import datetime

        records = [(p, json.loads(p.read_text())) for p in self.root.glob("*.json")]
        newest = {}
        for p, meta in records:
            if meta["state"] == "success":
                key = (meta["interface"], meta["domain"], meta.get("endpoint", ""))
                if key not in newest or meta["time"] > newest[key][1]["time"]:
                    newest[key] = (p, meta)
        pinned = {p for p, _ in newest.values()}
        removed = []
        for p, meta in records:
            if p in pinned or meta["state"] == "active":
                continue
            if meta["state"] == "success" or datetime.fromisoformat(meta["time"]) < now - timedelta(
                days=7
            ):
                data = p.with_suffix(".data")
                data.unlink(missing_ok=True)
                p.unlink()
                removed.append(data)
        return removed


def _elements(source, on_root=None, projection=None, validate_element=None):
    stack = []
    nodes = []
    for event, element in iterparse(source, events=("start", "end"), forbid_dtd=True):
        check_abort()
        if event == "start":
            if projection:
                if not nodes:
                    node = projection(element.tag)
                elif nodes[-1] is None:
                    node = None
                else:
                    node = nodes[-1].child(element.tag)
                    if nodes[-1].text:
                        stack[-1].text = None
                nodes.append(node)
                if node is not None:
                    for attr in tuple(element.attrib):
                        if not node.allows_attribute(attr):
                            del element.attrib[attr]
            if not stack and on_root:
                on_root(element)
            stack.append(element)
            continue
        if validate_element:
            validate_element(element)
        if projection:
            node = nodes.pop()
            element.tail = None
            if node is None:
                element.clear()
                stack.pop()
                if stack:
                    stack[-1].remove(element)
                continue
            if not node.text:
                element.text = None
            for child in element:
                child.tail = None
        had_content = bool(len(element) or element.attrib or element.text)
        yield element
        stack.pop()
        # A caller-cleared record must not accumulate as an empty node in its parent.
        if stack and had_content and not (len(element) or element.attrib or element.text):
            stack[-1].remove(element)


@contextmanager
def bounded_archive(stream, max_expanded):
    # CPython reads ZIP64 end records here without allocating the central directory.
    end = zipfile._EndRecData(stream)
    if end is None:
        raise zipfile.BadZipFile()
    if end[zipfile._ECD_ENTRIES_TOTAL] > 100 or end[zipfile._ECD_SIZE] > 512 * 1024:
        raise CatalogError("payload_too_large")
    with zipfile.ZipFile(stream) as archive:
        entries = archive.infolist()
        if len(entries) > 100 or sum(e.file_size for e in entries) > max_expanded:
            raise CatalogError("payload_too_large")
        yield archive


def parse_xml(
    path: Path, max_expanded=1024**3, on_root=None, projection=None, validate_element=None
):
    """Yield complete end elements; callers may clear processed record elements."""
    try:
        if zipfile.is_zipfile(path):
            with path.open("rb") as stream, bounded_archive(stream, max_expanded) as archive:
                for entry in archive.infolist():
                    member = PurePosixPath(entry.filename)
                    if member.is_absolute() or ".." in member.parts or "\\" in entry.filename:
                        raise CatalogError("unsafe_archive")
                    if entry.is_dir():
                        continue
                    with archive.open(entry) as source:
                        yield from _elements(source, on_root, projection, validate_element)
        else:
            if path.stat().st_size > max_expanded:
                raise CatalogError("payload_too_large")
            yield from _elements(path, on_root, projection, validate_element)
    except (DefusedXmlException, ParseError, zipfile.BadZipFile, OSError):
        raise CatalogError("invalid_export") from None
