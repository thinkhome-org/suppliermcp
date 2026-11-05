"""Source-isolated refreshes and PostgreSQL-backed scheduling."""

import json
from pathlib import Path

import procrastinate
from psycopg.types.json import Jsonb

from suppliermcp.catalog.contracts import CatalogError, utcnow
from suppliermcp.catalog.db import connect
from suppliermcp.config import Settings
from suppliermcp.suppliers.ed.gateway import READS, EdGateway
from suppliermcp.suppliers.ed.private import EdPrivateAdapter
from suppliermcp.suppliers.ed.public import EdPublicAdapter
from suppliermcp.suppliers.mega.adapter import MegaAdapter
from suppliermcp.suppliers.transport import SupplierTransport
from suppliermcp.sync.artifacts import ArtifactStore

from .publish import publish, stage


def source_contracts(settings):
    return (
        json.loads(settings.source_contracts_path.read_text())
        if settings.source_contracts_path
        else {}
    )


def build_adapters(settings):
    adapters, contracts = {}, source_contracts(settings)
    for interface, (login, password) in settings.credentials.items():
        options = contracts.get(interface, {})
        store = ArtifactStore(settings.artifact_dir, budget=settings.artifact_budget)
        if interface == "mega":
            transport = SupplierTransport(
                {"i6ws.100mega.cz"},
                {"GetResult", "GetResultByCode", "GetResultByFromTo"},
                auth=(login.get_secret_value(), password.get_secret_value()),
            )
            adapters[interface] = MegaAdapter(transport, store, options.get("exports", {}))
        else:
            host = ("public" if interface == "ed_public" else "private") + "-ws-cz.elinkx.biz"
            transport = SupplierTransport(
                {host, *options.get("download_hosts", [])}, READS | {"download"}
            )
            gateway = EdGateway(
                transport,
                "https://" + host + "/service.asmx",
                login.get_secret_value(),
                password.get_secret_value(),
            )
            cls = EdPublicAdapter if interface == "ed_public" else EdPrivateAdapter
            adapters[interface] = cls(gateway, store, transport)
    for adapter in adapters.values():
        adapter.max_expanded_bytes = settings.max_expanded_bytes
        adapter.max_description_bytes = settings.max_description_bytes
        adapter.transport.max_bytes = settings.max_download_bytes
    return adapters


def run_refresh(conn, adapter, domain, codes=None):
    now, manifest = utcnow(), None
    try:
        manifest = adapter.fetch(domain, codes)
        run_id = stage(conn, manifest, adapter.parse(manifest))
        revision = publish(conn, run_id)
        if getattr(adapter, "store", None) and manifest.path:
            adapter.store.mark(Path(manifest.path), "success", manifest)
        outcome = "ok"
        if adapter.interface == "ed_private" and domain == "catalog" and not codes:
            manifests, failures = adapter.enrichment()
            if hasattr(adapter, "dictionaries"):
                dictionaries, dictionary_failures = adapter.dictionaries()
                manifests.extend(dictionaries)
                failures.extend(dictionary_failures)
            for chunk in manifests:
                try:
                    revision = publish(conn, stage(conn, chunk, adapter.parse(chunk)))
                    if adapter.store and chunk.path:
                        adapter.store.mark(Path(chunk.path), "success", chunk)
                except CatalogError:
                    failures.append("chunk_failed")
                    if adapter.store and chunk.path:
                        adapter.store.mark(Path(chunk.path), "failed", chunk)
            if failures:
                outcome = "partial"

    except Exception as exc:
        outcome = exc.code if isinstance(exc, CatalogError) else "refresh_failed"
        if manifest and getattr(adapter, "store", None) and manifest.path:
            adapter.store.mark(Path(manifest.path), "failed", manifest)
        # Mark every price observation for this interface unavailable without replacing its value.
        conn.execute(
            "UPDATE current_offers SET data=jsonb_set(data,'{refresh_failed}','true') WHERE interface=%s",
            (adapter.interface,),
        )
        raise CatalogError(outcome, retryable=True) from None
    finally:
        state = {"configured": True, "outcome": outcome, "attempted_at": now.isoformat()}
        conn.execute(
            "INSERT INTO source_state VALUES (%s,%s) ON CONFLICT(interface) DO UPDATE SET data=EXCLUDED.data",
            (adapter.interface, Jsonb(state)),
        )
    return revision


def create_app(settings):
    app = procrastinate.App(
        connector=procrastinate.PsycopgConnector(conninfo=settings.database_url.get_secret_value())
    )

    @app.task(
        name="suppliermcp.refresh", retry=procrastinate.RetryStrategy(max_attempts=3, wait=60)
    )
    def refresh(interface, domain, codes=None):
        adapters = build_adapters(settings)
        if interface not in adapters:
            raise CatalogError("source_not_configured")
        with connect(settings) as conn:
            return run_refresh(conn, adapters[interface], domain, codes)

    @app.task(name="suppliermcp.index", retry=procrastinate.RetryStrategy(max_attempts=3, wait=60))
    def index():
        from suppliermcp.search.index import ALIAS, configured_client, drain_outbox, rebuild_index

        client = configured_client(settings)
        try:
            with connect(settings) as conn:
                aliases = client.request("GET", "/aliases").json()["aliases"]
                if not any(a["name"] == ALIAS for a in aliases):
                    rebuild_index(conn, client)
                return drain_outbox(conn, client)
        finally:
            client.http.close()

    @app.periodic(cron="* * * * *")
    @app.task(name="suppliermcp.tick")
    def tick(timestamp):
        try:
            index.configure(lock="index", queueing_lock="index").defer()
        except procrastinate.AlreadyEnqueued:
            pass
        contracts = source_contracts(settings)
        with connect(settings) as conn:
            conn.execute("DELETE FROM query_results WHERE expires_at < now()")
            ArtifactStore(settings.artifact_dir, budget=settings.artifact_budget).prune(utcnow())
            for interface in settings.enabled_interfaces:
                for domain, interval in (
                    contracts.get(interface, {}).get("intervals_seconds", {}).items()
                ):
                    if domain not in {"catalog", "price", "stock", "schema"} or interval < 60:
                        continue
                    row = conn.execute(
                        "SELECT started_at FROM domain_checkpoints WHERE interface=%s AND domain=%s",
                        (interface, domain),
                    ).fetchone()
                    if not row or (utcnow() - row[0]).total_seconds() >= interval:
                        try:
                            refresh.configure(
                                lock=("supplier:mega" if interface == "mega" else "supplier:ed"),
                                queueing_lock=f"{interface}:{domain}",
                            ).defer(interface=interface, domain=domain)
                        except procrastinate.AlreadyEnqueued:
                            pass

    return app


def schedule_refresh(interface, domain, codes=None, settings=None):
    settings = settings or Settings.from_env()
    if interface not in settings.enabled_interfaces:
        raise CatalogError("source_not_configured")
    app = create_app(settings)
    with app.open():
        return (
            app.tasks["suppliermcp.refresh"]
            .configure(
                lock=("supplier:mega" if interface == "mega" else "supplier:ed"),
                queueing_lock=f"{interface}:{domain}",
            )
            .defer(interface=interface, domain=domain, codes=codes)
        )
