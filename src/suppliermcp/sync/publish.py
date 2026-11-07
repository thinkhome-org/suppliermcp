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

BULK_ANALYZE_ITEMS = 10_000


def _class_export(manifest):
    return (
        manifest.interface == "mega"
        and manifest.mode == "full"
        and manifest.endpoint.removesuffix("_El") == "X-StoItemClass"
    )


def stage(conn, manifest, rows):
    run_id = uuid4()
    with conn.transaction():
        conn.execute(
            "INSERT INTO import_runs VALUES (%s,%s,%s,NULL,NULL)",
            (run_id, Jsonb(manifest.model_dump(mode="json")), "staging"),
        )
        with conn.cursor().copy("COPY staging (run_id,ordinal,kind,data) FROM STDIN") as copy:
            for ordinal, row in enumerate(rows):
                if isinstance(row, SchemaRecord) and row.kind == "product_facts":
                    from suppliermcp.catalog.contracts import Observation

                    row.values["observations"] = [
                        Observation.model_validate(o).model_dump(mode="json")
                        for o in row.values["observations"]
                    ]
                copy.write_row(
                    (run_id, ordinal, type(row).__name__, Jsonb(row.model_dump(mode="json")))
                )
        conn.execute(
            """UPDATE staging t SET data=jsonb_set(t.data,'{values,item_id}',to_jsonb(s.id))
            FROM (SELECT min(id) id,data->>'supplier' supplier,data->>'sku' sku FROM source_items
                WHERE active GROUP BY data->>'supplier',data->>'sku' HAVING count(*)=1) s
            WHERE t.run_id=%s AND t.kind='SchemaRecord'
            AND t.data->>'kind'='product_facts' AND t.data->'values'->>'item_id' IS NULL
            AND s.supplier=t.data->'values'->>'supplier'
            AND s.sku=t.data->'values'->>'sku'""",
            (run_id,),
        )
        if _class_export(manifest):
            # Supplier class lists can include SKUs outside the active account catalog.
            conn.execute(
                """UPDATE staging SET data=jsonb_set(data,'{kind}','"unmatched_product_class"')
                WHERE run_id=%s AND kind='SchemaRecord' AND data->>'kind'='product_facts'
                AND data->'values'->>'item_id' IS NULL""",
                (run_id,),
            )
        if conn.execute(
            "SELECT 1 FROM staging WHERE run_id=%s AND kind='SchemaRecord' AND data->>'kind'='product_facts' AND data->'values'->>'item_id' IS NULL LIMIT 1",
            (run_id,),
        ).fetchone():
            raise CatalogError("unresolved_product_reference")
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
        conn.execute("SET LOCAL work_mem = '64MB'")
        record = conn.execute(
            "SELECT manifest,status,revision FROM import_runs WHERE id=%s FOR UPDATE", (run_id,)
        ).fetchone()
        if not record:
            raise CatalogError("import_not_found")
        manifest = BatchManifest.model_validate(record[0])
        if record[1] in {"published", "unchanged", "superseded"}:
            return record[2]
        checkpoint = conn.execute(
            "SELECT started_at,artifact_sha256,revision,import_scope FROM endpoint_checkpoints WHERE interface=%s AND domain=%s AND endpoint=%s",
            (manifest.interface, manifest.domain, manifest.endpoint),
        ).fetchone()
        identities = [
            r[0]
            for r in conn.execute(
                "SELECT DISTINCT COALESCE(data->>'item_id',data->'values'->>'item_id',(data->>'supplier') || ':' || (data->>'source_id')) FROM staging WHERE run_id=%s AND (kind IN ('SourceItem','Offer') OR (kind='SchemaRecord' AND data->>'kind'='product_facts'))",
                (run_id,),
            )
        ]
        replace_ids = set(identities)
        for sku in manifest.requested_skus:
            supplier = "mega" if manifest.interface == "mega" else "ed"
            matches = {
                row[0]
                for row in conn.execute(
                    "SELECT id FROM source_items WHERE active AND data->>'supplier'=%s AND data->>'sku'=%s UNION SELECT (data->>'supplier') || ':' || (data->>'source_id') FROM staging WHERE run_id=%s AND kind='SourceItem' AND data->>'supplier'=%s AND data->>'sku'=%s",
                    (supplier, sku, run_id, supplier, sku),
                )
            }
            if len(matches) != 1:
                raise CatalogError("unresolved_product_reference")
            replace_ids.update(matches)
        replace_ids = list(replace_ids)
        if checkpoint and manifest.started_at <= checkpoint[0]:
            conn.execute(
                "UPDATE import_runs SET status='superseded',revision=%s WHERE id=%s",
                (checkpoint[2], run_id),
            )
            conn.execute("DELETE FROM staging WHERE run_id=%s", (run_id,))
            return checkpoint[2]
        scope_fields = {
            "mode",
            "requested_skus",
            "replace_scope",
            "authoritative_identity",
            "complete",
            "stock_only",
            "delta_from",
            "delta_to",
        }
        import_scope = manifest.model_dump(mode="json", include=scope_fields)
        if (
            checkpoint
            and import_scope == checkpoint[3]
            and manifest.artifact_sha256
            and manifest.artifact_sha256 == checkpoint[1]
            and not _class_export(manifest)
        ):
            scope = " AND item_id=ANY(%s)" if manifest.mode == "targeted" else ""
            args = (manifest.interface, manifest.endpoint) + ((replace_ids,) if scope else ())
            conn.execute(
                "UPDATE current_offers SET data=jsonb_set(data,'{refresh_failed}','false') WHERE interface=%s AND endpoint=%s"
                + scope,
                args,
            )

            conn.execute(
                "UPDATE endpoint_checkpoints SET started_at=%s WHERE interface=%s AND domain=%s AND endpoint=%s",
                (manifest.started_at, manifest.interface, manifest.domain, manifest.endpoint),
            )
            conn.execute(
                "UPDATE import_runs SET status='unchanged',revision=%s WHERE id=%s",
                (checkpoint[2], run_id),
            )
            conn.execute("DELETE FROM staging WHERE run_id=%s", (run_id,))
            conn.execute(
                "UPDATE domain_checkpoints SET started_at=GREATEST(started_at,%s) WHERE interface=%s AND domain=%s",
                (manifest.started_at, manifest.interface, manifest.domain),
            )
            return checkpoint[2]
        authoritative = (
            manifest.authoritative_identity
            if manifest.authoritative_identity is not None
            else manifest.domain == "catalog"
        )
        previous = conn.execute(
            "SELECT count(*) FROM source_presence WHERE interface=%s", (manifest.interface,)
        ).fetchone()[0]
        if (
            authoritative
            and manifest.domain == "catalog"
            and manifest.mode == "full"
            and manifest.complete
        ):
            if not identities or previous and len(set(identities)) < previous * 0.75:
                if not accept_reason:
                    conn.execute(
                        "UPDATE import_runs SET status='quarantined' WHERE id=%s", (run_id,)
                    )
                    quarantine = True
        if not quarantine:
            revision = conn.execute("SELECT nextval('catalog_revision')").fetchone()[0]
            changed = set()
            dictionary_fields = set()
            if manifest.replace_scope != "none":
                scoped = "" if manifest.replace_scope == "endpoint" else " AND item_id=ANY(%s)"
                args = (manifest.interface, manifest.endpoint) + (
                    () if not scoped else (replace_ids,)
                )
                for table in ["observations", "relationships"]:
                    removed = conn.execute(
                        f"DELETE FROM {table} WHERE interface=%s AND endpoint=%s"
                        + scoped
                        + " RETURNING item_id",
                        args,
                    )
                    changed.update(r[0] for r in removed)
                if manifest.replace_scope == "endpoint":
                    for kind, data in conn.execute(
                        "SELECT kind,data FROM source_schema WHERE interface=%s AND endpoint=%s AND kind IN ('parameter','SCategorySys','SCategorySys_El')",
                        (manifest.interface, manifest.endpoint),
                    ):
                        dictionary_fields.add(
                            "native:mega:parameter:" + data["code"]
                            if kind == "parameter"
                            else "native:mega:ScaId"
                        )
                    conn.execute(
                        "DELETE FROM source_schema WHERE interface=%s AND endpoint=%s",
                        (manifest.interface, manifest.endpoint),
                    )
            conn.execute(
                """
                INSERT INTO observations (item_id,interface,endpoint,field,data,value_key)
                SELECT DISTINCT ON (item_id,interface,endpoint,field,value_key)
                    item_id,interface,endpoint,field,observation,value_key
                FROM (
                    SELECT COALESCE(s.data->>'item_id',s.data->'values'->>'item_id',(s.data->>'supplier') || ':' || (s.data->>'source_id')) item_id,
                        o->>'interface' interface,o->>'endpoint' endpoint,o->>'field' field,
                        COALESCE(o->>'value_key','') value_key,o observation,s.ordinal
                    FROM staging s CROSS JOIN LATERAL jsonb_array_elements(COALESCE(s.data->'observations',s.data->'values'->'observations')) o
                    WHERE s.run_id=%s AND (s.kind IN ('SourceItem','Offer') OR (s.kind='SchemaRecord' AND s.data->>'kind'='product_facts'))
                        AND o->>'state' NOT IN ('missing','placeholder')
                ) facts ORDER BY item_id,interface,endpoint,field,value_key,ordinal DESC
                ON CONFLICT(item_id,interface,endpoint,field,value_key) DO UPDATE SET data=EXCLUDED.data
                """,
                (run_id,),
            )
            seen = {}
            cursor = conn.cursor(name="publish_rows")
            cursor.execute(
                "SELECT kind,data FROM staging WHERE run_id=%s ORDER BY ordinal", (run_id,)
            )
            for kind, data in cursor:
                if kind == "SchemaRecord":
                    schema = SchemaRecord.model_validate(data)
                    if schema.kind in {"SCategorySys", "SCategorySys_El"}:
                        dictionary_fields.add("native:mega:ScaId")
                    elif schema.kind == "parameter":
                        dictionary_fields.add("native:mega:parameter:" + schema.values["code"])
                    if schema.kind == "product_facts":
                        changed.add(schema.values["item_id"])
                        continue
                    if schema.kind == "relationship":
                        rel = schema.values
                        conn.execute(
                            "INSERT INTO relationships VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT(item_id,target_id,kind,interface,endpoint) DO UPDATE SET data=EXCLUDED.data",
                            (
                                rel["item_id"],
                                rel["target_id"],
                                rel["kind"],
                                Jsonb(rel),
                                manifest.interface,
                                manifest.endpoint,
                            ),
                        )
                    key = hashlib.sha256(str(sorted(schema.values.items())).encode()).hexdigest()
                    conn.execute(
                        "INSERT INTO source_schema VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                        (
                            schema.interface,
                            schema.kind,
                            key,
                            Jsonb(schema.values),
                            manifest.endpoint,
                        ),
                    )
                    continue
                if kind == "SourceItem":
                    item = SourceItem.model_validate(data)
                    signature = hashlib.sha256(str(data).encode()).digest()
                    if item.item_id in seen and seen[item.item_id] != signature:
                        raise CatalogError("conflicting_duplicate")
                    seen[item.item_id] = signature
                    old = conn.execute(
                        "SELECT data FROM source_items WHERE id=%s", (item.item_id,)
                    ).fetchone()
                    if old:
                        if old[0]["sku"] != item.sku:
                            raise CatalogError("identity_conflict")
                        for key in ["name", "manufacturer", "mpn", "ean"]:
                            if not data.get(key):
                                data[key] = old[0].get(key)
                    data["observations"] = []
                    conn.execute(
                        "INSERT INTO source_items VALUES (%s,%s,true,%s) ON CONFLICT(id) DO UPDATE SET data=EXCLUDED.data,active=true,revision=EXCLUDED.revision",
                        (item.item_id, Jsonb(data), revision),
                    )
                    conn.execute(
                        "INSERT INTO source_presence VALUES (%s,%s) ON CONFLICT DO NOTHING",
                        (item.item_id, manifest.interface),
                    )
                    changed.add(item.item_id)
                elif kind == "Offer":
                    offer = Offer.model_validate(data)
                    if offer.stock_state != "unknown":
                        data["stock_evidence_at"] = (
                            offer.stock_evidence_at or offer.evidence_at
                        ).isoformat()
                    prior = conn.execute(
                        "SELECT data FROM current_offers WHERE item_id=%s AND interface=%s AND domain=%s AND endpoint=%s",
                        (offer.item_id, manifest.interface, manifest.domain, manifest.endpoint),
                    ).fetchone()
                    if prior:
                        if offer.stock_state == "unknown":
                            for key in ["stock_state", "stock_qty", "stock_evidence_at"]:
                                data[key] = prior[0].get(key)
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
                    data["observations"] = []
                    conn.execute(
                        "INSERT INTO current_offers VALUES (%s,%s,%s,%s,%s) ON CONFLICT(item_id,interface,domain,endpoint) DO UPDATE SET data=EXCLUDED.data",
                        (
                            offer.item_id,
                            manifest.interface,
                            manifest.domain,
                            Jsonb(data),
                            manifest.endpoint,
                        ),
                    )
                    changed.add(offer.item_id)
            if manifest.complete and manifest.mode == "full":
                if manifest.domain == "catalog" and authoritative:
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
                            stock_evidence_at=manifest.started_at,
                        )
                        conn.execute(
                            "INSERT INTO current_offers VALUES (%s,%s,'stock',%s,%s) ON CONFLICT(item_id,interface,domain,endpoint) DO UPDATE SET data=current_offers.data || jsonb_build_object('stock_qty','0','stock_state','out_of_stock','stock_evidence_at',%s::text)",
                            (
                                item_id,
                                manifest.interface,
                                Jsonb(stock.model_dump(mode="json")),
                                manifest.endpoint,
                                manifest.started_at.isoformat(),
                            ),
                        )
                        changed.add(item_id)
            if dictionary_fields:
                changed.update(
                    r[0]
                    for r in conn.execute(
                        "SELECT DISTINCT item_id FROM catalog_values WHERE field=ANY(%s)",
                        (list(dictionary_fields),),
                    )
                )
            from suppliermcp.search.schema import refresh_values

            # At 10k items the projection below does 50 batches in this transaction,
            # before autovacuum can see these writes. Smaller imports use existing stats.
            if len(changed) >= BULK_ANALYZE_ITEMS:
                conn.execute("ANALYZE source_items, observations, current_offers")
            refresh_values(conn, changed)
            with conn.cursor().copy("COPY index_outbox (item_id, revision) FROM STDIN") as outbox:
                for item_id in changed:
                    outbox.write_row((item_id, revision))
            cursor.close()
            conn.execute(
                "INSERT INTO endpoint_checkpoints VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(interface,domain,endpoint) DO UPDATE SET started_at=EXCLUDED.started_at,artifact_sha256=EXCLUDED.artifact_sha256,revision=EXCLUDED.revision,delta_to=COALESCE(EXCLUDED.delta_to,endpoint_checkpoints.delta_to),import_scope=EXCLUDED.import_scope",
                (
                    manifest.interface,
                    manifest.domain,
                    manifest.endpoint,
                    manifest.started_at,
                    manifest.artifact_sha256,
                    revision,
                    manifest.delta_to,
                    Jsonb(import_scope),
                ),
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
