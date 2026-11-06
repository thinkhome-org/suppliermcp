"""Source-isolated refreshes and PostgreSQL-backed scheduling."""

import json
from itertools import chain
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
from suppliermcp.suppliers.mega.capabilities import account_exports
from suppliermcp.suppliers.profiles import SERVICES
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
    for interface in settings.enabled_interfaces:
        options = contracts.get(interface, {})
        store = ArtifactStore(settings.artifact_dir, budget=settings.artifact_budget)
        profile = SERVICES[interface]
        login, password = settings.credentials[profile.account]
        if interface == "mega":
            transport = SupplierTransport(
                {profile.host},
                {"GetResult", "GetResultByCode", "GetResultByFromTo"},
                auth=(login.get_secret_value(), password.get_secret_value()),
            )
            adapters[interface] = MegaAdapter(
                transport, store, account_exports(options, login.get_secret_value(), profile)
            )
        else:
            transport = SupplierTransport(
                {profile.host, *options.get("download_hosts", [])}, READS | {"download"}
            )
            gateway = EdGateway(
                transport,
                profile.url,
                login.get_secret_value(),
                password.get_secret_value(),
            )
            cls = EdPublicAdapter if interface == "ed_public" else EdPrivateAdapter
            adapters[interface] = cls(gateway, store, transport)
            adapters[interface].offer_contract = options.get("offer", {})
    for adapter in adapters.values():
        adapter.max_expanded_bytes = settings.max_expanded_bytes
        adapter.max_description_bytes = settings.max_description_bytes
        adapter.transport.max_bytes = settings.max_download_bytes
        adapter.transport.download_timeout = settings.download_timeout_seconds
    return adapters


def run_export_refresh(conn, adapter, endpoint, codes=None):
    domain = next((d for d, e in adapter.endpoints.items() if e == endpoint), "schema")
    return run_refresh(conn, adapter, domain, codes, endpoint=endpoint)


def run_refresh(conn, adapter, domain, codes=None, *, endpoint=None):
    source_endpoint = endpoint or getattr(
        adapter, "endpoints", getattr(adapter, "methods", {})
    ).get(domain, domain)
    if codes and adapter.interface == "ed_private":
        source_endpoint = "getProductDetail"
    # Each installation has one configured account per interface.
    lock_key = f"suppliermcp.refresh:{adapter.interface}:{source_endpoint}"
    if not conn.execute(
        "SELECT pg_try_advisory_lock(hashtextextended(%s, 0))", (lock_key,)
    ).fetchone()[0]:
        raise CatalogError("refresh_in_progress", retryable=True)
    try:
        return _run_refresh(conn, adapter, domain, codes, endpoint, source_endpoint)
    finally:
        conn.execute("SELECT pg_advisory_unlock(hashtextextended(%s, 0))", (lock_key,))


def _run_refresh(conn, adapter, domain, codes, endpoint, source_endpoint):
    now, manifest = utcnow(), None
    revision = None
    outcome = "refresh_failed"
    try:
        manifest = (
            adapter.fetch_export(endpoint, codes=codes)
            if endpoint
            else adapter.fetch(domain, codes)
        )
        source_endpoint = manifest.endpoint or source_endpoint
        domain = manifest.domain
        manifest.started_at = now
        run_id = stage(conn, manifest, adapter.parse(manifest))
        revision = publish(conn, run_id)
        if getattr(adapter, "store", None) and manifest.path:
            adapter.store.mark(Path(manifest.path), "success", manifest)
        outcome = "ok"
        if adapter.interface == "ed_private" and domain == "catalog" and not codes:
            manifests, failures = adapter.enrichment()
            if hasattr(adapter, "dictionaries"):
                dictionaries, dictionary_failures = adapter.dictionaries()
                manifests = chain(manifests, dictionaries)
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
            "UPDATE current_offers SET data=jsonb_set(data,'{refresh_failed}','true') WHERE interface=%s AND (endpoint=%s OR (endpoint='' AND %s))",
            (adapter.interface, source_endpoint, domain != "schema"),
        )
        raise CatalogError(outcome, retryable=True) from None
    finally:
        record_refresh_outcome(
            conn, adapter, domain, source_endpoint, now, outcome, manifest, revision, codes
        )

    return revision


def locked_source_state(conn, interface):
    """Called inside a transaction; serialize updates to the same interface JSON."""
    conn.execute(
        "INSERT INTO source_state VALUES (%s, '{}'::jsonb) ON CONFLICT DO NOTHING", (interface,)
    )
    return conn.execute(
        "SELECT data FROM source_state WHERE interface=%s FOR UPDATE", (interface,)
    ).fetchone()[0]


def record_refresh_outcome(
    conn, adapter, domain, source_endpoint, now, outcome, manifest, revision, codes=None
):
    with conn.transaction():
        state = locked_source_state(conn, adapter.interface)
        domains = state.setdefault("domains", {})
        previous_domain = domains.get(domain, {})
        complete = bool(
            manifest and manifest.complete and manifest.mode == "full" and outcome == "ok"
        )
        domains[domain] = {
            "outcome": outcome,
            "attempted_at": now.isoformat(),
            "complete": complete,
            "last_verified_complete_revision": revision
            if complete
            else previous_domain.get("last_verified_complete_revision"),
        }
        endpoints = state.setdefault("endpoints", {})
        prior_endpoint = endpoints.get(source_endpoint, {})
        next_allowed = None
        if outcome == "outside_supplier_window":
            from suppliermcp.suppliers.mega.capabilities import next_window

            mode = "targeted" if codes else "full"
            next_allowed = next_window(adapter.export_window(source_endpoint, mode), mode)
        endpoints[source_endpoint] = {
            "outcome": outcome,
            "attempted_at": now.isoformat(),
            "last_success_at": now.isoformat()
            if outcome == "ok"
            else prior_endpoint.get("last_success_at"),
            "next_allowed_at": next_allowed.isoformat() if next_allowed else None,
            "complete": complete,
            "revision": revision if outcome == "ok" else prior_endpoint.get("revision"),
        }
        state.update(
            configured=True,
            attempted_at=now.isoformat(),
            outcome="ok" if all(d["outcome"] == "ok" for d in endpoints.values()) else "partial",
        )
        if outcome not in {"ok", "partial"}:
            state["outcome"] = outcome
        conn.execute(
            "INSERT INTO source_state VALUES (%s,%s) ON CONFLICT(interface) DO UPDATE SET data=EXCLUDED.data",
            (adapter.interface, Jsonb(state)),
        )


def create_app(settings):
    app = procrastinate.App(
        connector=procrastinate.PsycopgConnector(conninfo=settings.database_url.get_secret_value())
    )

    @app.task(
        name="suppliermcp.refresh", retry=procrastinate.RetryStrategy(max_attempts=3, wait=60)
    )
    def refresh(interface, domain, codes=None, endpoint=None):
        adapters = build_adapters(settings)
        if interface not in adapters:
            raise CatalogError("source_not_configured")
        with connect(settings) as conn:
            return run_refresh(conn, adapters[interface], domain, codes, endpoint=endpoint)

    @app.task(name="suppliermcp.index", retry=procrastinate.RetryStrategy(max_attempts=3, wait=60))
    def index():
        from suppliermcp.search.index import (
            ALIAS,
            SEARCH_FIELDS,
            configured_client,
            drain_pending,
            rebuild_index,
        )

        client = configured_client(settings)
        try:
            with connect(settings) as conn:
                collection = client.request("GET", f"/collections/{ALIAS}", allow_missing=True)
                required = {*SEARCH_FIELDS, "unknown_facets", "verified", "supplier", "revision"}
                if collection.status_code == 404 or not required.issubset(
                    f["name"] for f in collection.json()["fields"]
                ):
                    rebuild_index(conn, client)
                return drain_pending(conn, client)
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
            adapters = build_adapters(settings)
            for interface, adapter in adapters.items():
                options = contracts.get(interface, {})
                schedules = [
                    (domain, None, interval)
                    for domain, interval in options.get("intervals_seconds", {}).items()
                ]
                schedules += [
                    ("schema", endpoint, interval)
                    for endpoint, interval in options.get("export_intervals_seconds", {}).items()
                ]
                for domain, endpoint, interval in schedules:
                    if domain not in {"catalog", "price", "stock", "schema"} or interval < 60:
                        continue
                    source_endpoint = endpoint or getattr(
                        adapter, "endpoints", getattr(adapter, "methods", {})
                    ).get(domain, domain)
                    state_row = conn.execute(
                        "SELECT data FROM source_state WHERE interface=%s", (interface,)
                    ).fetchone()
                    state = state_row[0] if state_row else {}
                    last = state.get("endpoints", {}).get(source_endpoint, {}).get("attempted_at")
                    if last:
                        from datetime import datetime

                        if (utcnow() - datetime.fromisoformat(last)).total_seconds() < interval:
                            continue
                    if interface == "mega":
                        from suppliermcp.suppliers.mega.capabilities import (
                            next_window,
                            require_window,
                        )

                        contract = adapter.export_window(source_endpoint, "full")
                        try:
                            require_window(contract, "full")
                        except CatalogError as error:
                            upcoming = next_window(contract, "full")
                            with conn.transaction():
                                state = locked_source_state(conn, interface)
                                entry = state.setdefault("endpoints", {}).setdefault(
                                    source_endpoint, {}
                                )
                                entry.update(
                                    outcome=error.code,
                                    next_allowed_at=upcoming.isoformat() if upcoming else None,
                                )
                                state["configured"] = True
                                conn.execute(
                                    "INSERT INTO source_state VALUES (%s,%s) ON CONFLICT(interface) DO UPDATE SET data=EXCLUDED.data",
                                    (interface, Jsonb(state)),
                                )
                            continue
                    try:
                        refresh.configure(
                            lock=("supplier:mega" if interface == "mega" else "supplier:ed"),
                            queueing_lock=f"{interface}:{source_endpoint}",
                        ).defer(interface=interface, domain=domain, endpoint=endpoint)
                    except procrastinate.AlreadyEnqueued:
                        pass

            for adapter in adapters.values():
                adapter.transport.client.close()

    return app


def schedule_refresh(interface, domain, codes=None, settings=None):
    settings = settings or Settings.from_env()
    if interface not in settings.enabled_interfaces:
        raise CatalogError("source_not_configured")
    if interface == "ed_public" and codes:
        raise CatalogError("unsupported_targeted_read")
    if interface == "mega":
        adapter = build_adapters(settings)[interface]
        from suppliermcp.suppliers.mega.capabilities import require_window

        mode = "targeted" if codes else "full"
        require_window(adapter.export_window(adapter.endpoints.get(domain), mode), mode)
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
