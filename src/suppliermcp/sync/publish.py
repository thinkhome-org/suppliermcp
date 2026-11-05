"""Atomic publication: no network calls while catalog locks are held."""

import hashlib
from uuid import uuid4

from psycopg.types.json import Jsonb

from suppliermcp.catalog.contracts import (
    BatchManifest,
    CatalogError,
    Offer,
    SchemaRecord,
    SourceItem,
)


def stage(conn, manifest, rows):
    run_id = uuid4()
    with conn.transaction():
        conn.execute(
            "INSERT INTO import_runs VALUES (%s,%s,%s,NULL,NULL)",
            (run_id, Jsonb(manifest.model_dump(mode="json")), "staging"),
        )
        for ordinal, row in enumerate(rows):
            conn.execute(
                "INSERT INTO staging VALUES (%s,%s,%s,%s)",
                (run_id, ordinal, type(row).__name__, Jsonb(row.model_dump(mode="json"))),
            )
        # Parsers establish completeness only after the stream has ended successfully.
        conn.execute(
            "UPDATE import_runs SET manifest=%s,status=%s WHERE id=%s",
            (Jsonb(manifest.model_dump(mode="json")), "staged", run_id),
        )
    return run_id


def publish(conn, run_id, *, accept_reason=None):
    quarantine = False
    with conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(91002)")
        record = conn.execute(
            "SELECT manifest,status,revision FROM import_runs WHERE id=%s FOR UPDATE", (run_id,)
        ).fetchone()
        if not record:
            raise CatalogError("import_not_found")
        manifest = BatchManifest.model_validate(record[0])
        if record[1] == "published":
            return record[2]
        checkpoint = conn.execute(
            "SELECT started_at,artifact_sha256,revision FROM domain_checkpoints WHERE interface=%s AND domain=%s",
            (manifest.interface, manifest.domain),
        ).fetchone()
        if checkpoint and manifest.started_at <= checkpoint[0]:
            conn.execute(
                "UPDATE import_runs SET status='superseded',revision=%s WHERE id=%s",
                (checkpoint[2], run_id),
            )
            return checkpoint[2]
        if checkpoint and manifest.artifact_sha256 and manifest.artifact_sha256 == checkpoint[1]:
            conn.execute(
                "UPDATE import_runs SET status='unchanged',revision=%s WHERE id=%s",
                (checkpoint[2], run_id),
            )
            return checkpoint[2]
        rows = conn.execute(
            "SELECT kind,data FROM staging WHERE run_id=%s ORDER BY ordinal", (run_id,)
        ).fetchall()
        identities = [SourceItem.model_validate(d).item_id for k, d in rows if k == "SourceItem"]
        previous = conn.execute(
            "SELECT count(*) FROM source_presence WHERE interface=%s", (manifest.interface,)
        ).fetchone()[0]
        if manifest.domain == "catalog" and manifest.mode == "full" and manifest.complete:
            if not identities or previous and len(set(identities)) < previous * 0.75:
                if not accept_reason:
                    conn.execute(
                        "UPDATE import_runs SET status='quarantined' WHERE id=%s", (run_id,)
                    )
                    quarantine = True
        if not quarantine:
            revision = conn.execute("SELECT nextval('catalog_revision')").fetchone()[0]
            changed = set()
            seen = {}
            for kind, data in rows:
                if kind == "SchemaRecord":
                    schema = SchemaRecord.model_validate(data)
                    if schema.kind == "relationship":
                        rel = schema.values
                        conn.execute(
                            "INSERT INTO relationships VALUES (%s,%s,%s,%s) ON CONFLICT(item_id,target_id,kind) DO UPDATE SET data=EXCLUDED.data",
                            (rel["item_id"], rel["target_id"], rel["kind"], Jsonb(rel)),
                        )
                    key = hashlib.sha256(str(sorted(schema.values.items())).encode()).hexdigest()
                    conn.execute(
                        "INSERT INTO source_schema VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                        (schema.interface, schema.kind, key, Jsonb(schema.values)),
                    )
                    continue
                if kind == "SourceItem":
                    item = SourceItem.model_validate(data)
                    if item.item_id in seen and seen[item.item_id] != data:
                        raise CatalogError("conflicting_duplicate")
                    seen[item.item_id] = data
                    old = conn.execute(
                        "SELECT data FROM source_items WHERE id=%s", (item.item_id,)
                    ).fetchone()
                    if old:
                        if old[0]["sku"] != item.sku:
                            raise CatalogError("identity_conflict")
                        for key in ["name", "manufacturer", "mpn", "ean"]:
                            if not data.get(key):
                                data[key] = old[0].get(key)
                    conn.execute(
                        "INSERT INTO source_items VALUES (%s,%s,true,%s) ON CONFLICT(id) DO UPDATE SET data=EXCLUDED.data,active=true,revision=EXCLUDED.revision",
                        (item.item_id, Jsonb(data), revision),
                    )
                    conn.execute(
                        "INSERT INTO source_presence VALUES (%s,%s) ON CONFLICT DO NOTHING",
                        (item.item_id, manifest.interface),
                    )
                    for o in item.observations:
                        if o.state in {"missing", "placeholder"}:
                            continue
                        conn.execute(
                            "INSERT INTO observations VALUES (%s,%s,%s,%s,%s) ON CONFLICT(item_id,interface,endpoint,field) DO UPDATE SET data=EXCLUDED.data",
                            (
                                item.item_id,
                                o.interface,
                                o.endpoint,
                                o.field,
                                Jsonb(o.model_dump(mode="json")),
                            ),
                        )
                    changed.add(item.item_id)
                elif kind == "Offer":
                    offer = Offer.model_validate(data)
                    prior = conn.execute(
                        "SELECT data FROM current_offers WHERE item_id=%s AND interface=%s AND domain=%s",
                        (offer.item_id, manifest.interface, manifest.domain),
                    ).fetchone()
                    if prior:
                        if offer.unit_net is None:
                            for key in [
                                "evidence_at",
                                "source_updated_at",
                                "price_rule",
                                "discount_min_qty",
                                "discount",
                                "freshness_seconds",
                            ]:
                                data[key] = prior[0].get(key)
                        for key, value in data.items():
                            if value is None:
                                data[key] = prior[0].get(key)
                    conn.execute(
                        "INSERT INTO current_offers VALUES (%s,%s,%s,%s) ON CONFLICT(item_id,interface,domain) DO UPDATE SET data=EXCLUDED.data",
                        (offer.item_id, manifest.interface, manifest.domain, Jsonb(data)),
                    )
                    changed.add(offer.item_id)
            if manifest.complete and manifest.mode == "full":
                if manifest.domain == "catalog":
                    conn.execute(
                        "DELETE FROM source_presence WHERE interface=%s AND NOT(item_id=ANY(%s))",
                        (manifest.interface, identities),
                    )
                    missing = conn.execute(
                        "UPDATE source_items SET active=false,revision=%s WHERE active AND NOT EXISTS(SELECT 1 FROM source_presence WHERE item_id=source_items.id) RETURNING id",
                        (revision,),
                    ).fetchall()
                    changed.update(r[0] for r in missing)
                elif manifest.domain == "stock" and manifest.stock_only:
                    for (item_id,) in conn.execute(
                        "SELECT s.id FROM source_items s JOIN source_presence p ON p.item_id=s.id WHERE p.interface=%s AND s.active AND NOT(s.id=ANY(%s))",
                        (manifest.interface, identities),
                    ).fetchall():
                        stock = Offer(
                            item_id=item_id,
                            stock_qty="0",
                            stock_state="out_of_stock",
                            evidence_at=manifest.started_at,
                        )
                        conn.execute(
                            "INSERT INTO current_offers VALUES (%s,%s,'stock',%s) ON CONFLICT(item_id,interface,domain) DO UPDATE SET data=current_offers.data || jsonb_build_object('stock_qty','0','stock_state','out_of_stock','fetched_at',%s::text)",
                            (
                                item_id,
                                manifest.interface,
                                Jsonb(stock.model_dump(mode="json")),
                                manifest.started_at.isoformat(),
                            ),
                        )
                        changed.add(item_id)
            from suppliermcp.search.schema import refresh_values

            refresh_values(conn, changed)
            for item_id in changed:
                conn.execute(
                    "INSERT INTO index_outbox(item_id,revision) VALUES (%s,%s)", (item_id, revision)
                )
            conn.execute(
                "INSERT INTO domain_checkpoints VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT(interface,domain) DO UPDATE SET started_at=EXCLUDED.started_at,artifact_sha256=EXCLUDED.artifact_sha256,revision=EXCLUDED.revision,delta_to=COALESCE(EXCLUDED.delta_to,domain_checkpoints.delta_to)",
                (
                    manifest.interface,
                    manifest.domain,
                    manifest.started_at,
                    manifest.artifact_sha256,
                    revision,
                    manifest.delta_to,
                ),
            )
            conn.execute(
                "UPDATE import_runs SET status='published',revision=%s,reason=%s WHERE id=%s",
                (revision, accept_reason, run_id),
            )
            conn.execute("DELETE FROM staging WHERE run_id=%s", (run_id,))
    if quarantine:
        raise CatalogError("import_quarantined")
    return revision
