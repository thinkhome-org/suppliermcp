-- V1 flattened XML without retaining its ancestor path. Even a typed SKU/price
-- could have originated in a customer record. Only a clean import proves scope.
DO $$
DECLARE
    source_table text;
    populated boolean;
BEGIN
    FOREACH source_table IN ARRAY ARRAY[
        'source_items', 'current_offers', 'observations', 'source_schema', 'relationships',
        'import_runs', 'staging', 'domain_checkpoints', 'source_state', 'index_outbox',
        'source_presence', 'product_links', 'catalog_values', 'query_results', 'query_cursors',
        'query_result_rows', 'endpoint_checkpoints'
    ] LOOP
        EXECUTE format('LOCK TABLE %I IN SHARE MODE', source_table);
        EXECUTE format('SELECT EXISTS (SELECT FROM %I LIMIT 1)', source_table) INTO populated;
        IF populated THEN
            RAISE EXCEPTION 'catalog_reprojection_required'
                USING HINT = 'Start a separate empty v2 database and Typesense volume. Reimport through the v2 adapters before cutover. See docs/operations.md. Keep the original stack and volumes for rollback.';
        END IF;
    END LOOP;
END $$;
