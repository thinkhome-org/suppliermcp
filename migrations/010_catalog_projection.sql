-- Old evidence lacks the XML ancestry needed to establish its catalogue scope.
-- Retain it for operators, and let verified refreshes repopulate the public tables.
SELECT pg_advisory_xact_lock(91003);
SELECT pg_advisory_xact_lock(91002);

ALTER TABLE observations RENAME TO legacy_unprojected_observations;
CREATE TABLE observations (LIKE legacy_unprojected_observations INCLUDING ALL);
ALTER TABLE source_schema RENAME TO legacy_unprojected_source_schema;
CREATE TABLE source_schema (LIKE legacy_unprojected_source_schema INCLUDING ALL);
ALTER TABLE relationships RENAME TO legacy_unprojected_relationships;
CREATE TABLE relationships (LIKE legacy_unprojected_relationships INCLUDING ALL);

ALTER TABLE catalog_values RENAME TO legacy_unprojected_catalog_values;
CREATE TABLE catalog_values (LIKE legacy_unprojected_catalog_values INCLUDING ALL);
ALTER TABLE catalog_values ADD FOREIGN KEY (item_id) REFERENCES source_items(id) ON DELETE CASCADE;
INSERT INTO catalog_values SELECT * FROM legacy_unprojected_catalog_values
WHERE field IN ('supplier','manufacturer','sku','ean','mpn','currency','price','stock_state','stock_qty');

-- Older releases could also store raw observations inside typed product and offer JSON.
CREATE TABLE legacy_unprojected_embedded AS
SELECT id AS item_id, NULL::text AS interface, NULL::text AS domain, NULL::text AS endpoint,
       data->'observations' AS observations FROM source_items
WHERE jsonb_array_length(data->'observations') > 0
UNION ALL
SELECT item_id, interface, domain, endpoint, data->'observations' FROM current_offers
WHERE jsonb_array_length(data->'observations') > 0;
UPDATE source_items SET data = data - 'observations' WHERE jsonb_array_length(data->'observations') > 0;
UPDATE current_offers SET data = data - 'observations' WHERE jsonb_array_length(data->'observations') > 0;

UPDATE import_runs SET status='requires_projection' WHERE status IN ('staged','quarantined','staging');
UPDATE endpoint_checkpoints SET import_scope=NULL;
DELETE FROM query_results;
