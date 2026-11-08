"""Source-isolated refreshes and PostgreSQL-backed scheduling."""

import json
from contextlib import contextmanager
from pathlib import Path

import procrastinate
from procrastinate.exceptions import AlreadyEnqueued
from psycopg.types.json import Jsonb

from suppliermcp.catalog.contracts import BatchManifest, CatalogError, utcnow
from suppliermcp.catalog.db import connect, connection_info
from suppliermcp.config import Settings
from suppliermcp.suppliers.ed.gateway import READS, EdGateway
from suppliermcp.suppliers.ed.private import EdPrivateAdapter
from suppliermcp.suppliers.ed.public import EdPublicAdapter
from suppliermcp.suppliers.mega.adapter import MegaAdapter
from suppliermcp.suppliers.mega.capabilities import account_exports
from suppliermcp.suppliers.profiles import SERVICES
from suppliermcp.suppliers.transport import SupplierTransport
from suppliermcp.sync.artifacts import ArtifactStore

from .lifecycle import abortable_job, check_abort
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
    with refresh_lock(conn, adapter.interface, source_endpoint):
        return _run_refresh(conn, adapter, domain, codes, endpoint, source_endpoint)


@contextmanager
def refresh_lock(conn, interface, endpoint):
    # Each installation has one configured account per interface.
    lock_key = f"suppliermcp.refresh:{interface}:{endpoint}"
    if not conn.execute(
        "SELECT pg_try_advisory_lock(hashtextextended(%s, 0))", (lock_key,)
    ).fetchone()[0]:
        raise CatalogError("refresh_in_progress", retryable=True)
    try:
        yield
    finally:
        conn.execute("SELECT pg_advisory_unlock(hashtextextended(%s, 0))", (lock_key,))


def _run_refresh(conn, adapter, domain, codes, endpoint, source_endpoint):
    now, manifest = utcnow(), None
    revision = None
    run_id = None
    outcome = "refresh_failed"
    try:
        private_catalog = adapter.interface == "ed_private" and domain == "catalog" and not codes
        cycle = (
            conn.execute(
                """SELECT r.id, r.manifest, r.revision FROM ed_commodity_cycles c
               JOIN import_runs r ON r.id=c.baseline_run_id WHERE NOT c.finished"""
            ).fetchone()
            if private_catalog
            else None
        )
        if cycle:
            run_id, saved_manifest, revision = cycle
            manifest = BatchManifest.model_validate(saved_manifest)
        else:
            manifest = (
                adapter.fetch_export(endpoint, codes=codes)
                if endpoint
                else adapter.fetch(domain, codes)
            )
            manifest.started_at = now
            run_id = stage(conn, manifest, adapter.parse(manifest))
            revision = publish(conn, run_id)
            if getattr(adapter, "store", None) and manifest.path:
                adapter.store.mark(Path(manifest.path), "success", manifest)
        source_endpoint = manifest.endpoint or source_endpoint
        domain = manifest.domain
        outcome = "ok"
        if private_catalog:
            outcome = "partial"
            if not cycle:
                expected = adapter.commodity_codes()
                if not expected:
                    raise CatalogError("commodity_list_empty")
                status = conn.execute(
                    "SELECT status FROM import_runs WHERE id=%s", (run_id,)
                ).fetchone()[0]
                if status not in {"published", "unchanged"} or not manifest.complete:
                    raise CatalogError("incomplete_baseline")
                with conn.transaction():
                    conn.execute(
                        "INSERT INTO ed_commodity_cycles(baseline_run_id) VALUES (%s)", (run_id,)
                    )
                    conn.execute(
                        """INSERT INTO ed_commodity_parts(baseline_run_id,code)
                                    SELECT %s, unnest(%s::text[])""",
                        (run_id, expected),
                    )
                    record_refresh_outcome(
                        conn, adapter, domain, source_endpoint, now, outcome, manifest, revision
                    )
            revision, outcome = _finish_private_catalog(conn, adapter, run_id, revision)

    except Exception as exc:
        check_abort()
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
        check_abort()
        with conn.transaction():
            if private_catalog and outcome == "ok":
                conn.execute(
                    "UPDATE ed_commodity_cycles SET finished=true WHERE baseline_run_id=%s",
                    (run_id,),
                )
                if conn.execute("SELECT to_regclass('procrastinate_jobs')").fetchone()[0]:
                    conn.execute(
                        """SELECT procrastinate_finish_job_v1(id,'aborted',false) FROM
                        (SELECT id FROM procrastinate_jobs WHERE task_name='suppliermcp.refresh'
                         AND queueing_lock=%s AND status='todo' FOR UPDATE) pending""",
                        (f"{adapter.interface}:{source_endpoint}",),
                    )
            record_refresh_outcome(
                conn, adapter, domain, source_endpoint, now, outcome, manifest, revision, codes
            )

    return revision


def _finish_private_catalog(conn, adapter, baseline, revision):
    pending = conn.execute(
        """SELECT code FROM ed_commodity_parts
           WHERE baseline_run_id=%s AND chunk_run_id IS NULL ORDER BY code""",
        (baseline,),
    ).fetchall()
    for (code,) in pending:
        chunk = None
        try:
            chunk = adapter.fetch_commodity(code)
            part = stage(conn, chunk, adapter.parse(chunk))
            with conn.transaction():
                empty = not conn.execute(
                    "SELECT 1 FROM staging WHERE run_id=%s LIMIT 1", (part,)
                ).fetchone()
                revision = publish(conn, part)
                status = conn.execute(
                    "SELECT status FROM import_runs WHERE id=%s", (part,)
                ).fetchone()[0]
                if status not in {"published", "unchanged"}:
                    raise CatalogError("commodity_not_published")
                conn.execute(
                    """UPDATE ed_commodity_parts SET chunk_run_id=%s, empty=%s
                                WHERE baseline_run_id=%s AND code=%s""",
                    (part, empty, baseline, code),
                )
            if adapter.store and chunk.path:
                adapter.store.mark(Path(chunk.path), "success", chunk)
        except CatalogError:
            if chunk and adapter.store and chunk.path:
                adapter.store.mark(Path(chunk.path), "failed", chunk)

    if conn.execute(
        """SELECT 1 FROM ed_commodity_parts WHERE baseline_run_id=%s
                       AND chunk_run_id IS NULL LIMIT 1""",
        (baseline,),
    ).fetchone():
        return revision, "partial"

    revision = conn.execute(
        """SELECT GREATEST(%s, max(r.revision)) FROM ed_commodity_parts p
                               JOIN import_runs r ON r.id=p.chunk_run_id WHERE baseline_run_id=%s""",
        (revision, baseline),
    ).fetchone()[0]
    dictionaries, failures = (
        adapter.dictionaries() if hasattr(adapter, "dictionaries") else ([], [])
    )
    for chunk in dictionaries:
        try:
            revision = max(revision, publish(conn, stage(conn, chunk, adapter.parse(chunk))))
            if adapter.store and chunk.path:
                adapter.store.mark(Path(chunk.path), "success", chunk)
        except CatalogError:
            failures.append(chunk.endpoint)
            if adapter.store and chunk.path:
                adapter.store.mark(Path(chunk.path), "failed", chunk)
    if failures:
        return revision, "partial"
    return revision, "ok"


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


def _scheduled_job_running(conn, task, key):
    # Procrastinate drops the owner after worker loss. Respect any live source/index lock too.
    with conn.transaction():
        job = conn.execute(
            """SELECT id, worker_id FROM procrastinate_jobs WHERE task_name=%s
                              AND queueing_lock=%s AND status='doing' FOR UPDATE""",
            (task, key),
        ).fetchone()
        if not job:
            return False
        if job[1] is not None:
            return True
        protected = (
            conn.execute("SELECT pg_try_advisory_xact_lock(91003)")
            if key == "index"
            else conn.execute(
                "SELECT pg_try_advisory_xact_lock(hashtextextended(%s,0))",
                ("suppliermcp.refresh:" + key,),
            )
        ).fetchone()[0]
        if protected:
            if conn.execute(
                "SELECT 1 FROM procrastinate_jobs WHERE queueing_lock=%s AND status='todo'", (key,)
            ).fetchone():
                conn.execute("SELECT procrastinate_finish_job_v1(%s,'aborted',false)", (job[0],))
            else:
                conn.execute(
                    "SELECT procrastinate_retry_job_v2(%s,now(),NULL,NULL,NULL)", (job[0],)
                )
        return True


def create_app(settings):
    app = procrastinate.App(
        connector=procrastinate.PsycopgConnector(conninfo=connection_info(settings))
    )

    @app.task(
        name="suppliermcp.refresh",
        pass_context=True,
        retry=procrastinate.RetryStrategy(max_attempts=3, wait=60),
    )
    @abortable_job
    def refresh(interface, domain, codes=None, endpoint=None):
        adapters = build_adapters(settings)
        if interface not in adapters:
            raise CatalogError("source_not_configured")
        with connect(settings) as conn:
            return run_refresh(conn, adapters[interface], domain, codes, endpoint=endpoint)

    @app.task(
        name="suppliermcp.index",
        pass_context=True,
        retry=procrastinate.RetryStrategy(max_attempts=3, wait=60),
    )
    @abortable_job
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
    @app.task(name="suppliermcp.tick", pass_context=True)
    @abortable_job
    def tick(timestamp):
        contracts = source_contracts(settings)
        with connect(settings) as conn:
            if not _scheduled_job_running(conn, "suppliermcp.index", "index"):
                try:
                    index.configure(lock="index", queueing_lock="index").defer()
                except AlreadyEnqueued:
                    pass
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
                    if _scheduled_job_running(
                        conn, "suppliermcp.refresh", f"{interface}:{source_endpoint}"
                    ):
                        continue
                    if interface == "ed_private" and domain == "catalog" and not endpoint:
                        if conn.execute(
                            "SELECT 1 FROM ed_commodity_cycles WHERE NOT finished"
                        ).fetchone():
                            interval = min(interval, 300)
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
                    except AlreadyEnqueued:
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
