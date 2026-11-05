CREATE TABLE IF NOT EXISTS catalog_values (item_id text REFERENCES source_items(id) ON DELETE CASCADE, field text NOT NULL, value text, state text NOT NULL, value_type text NOT NULL, PRIMARY KEY(item_id,field));
CREATE INDEX IF NOT EXISTS catalog_values_field ON catalog_values(field,value);
CREATE TABLE IF NOT EXISTS query_results (id text PRIMARY KEY, principal text NOT NULL, query_hash text NOT NULL, expires_at timestamptz NOT NULL, data jsonb NOT NULL);
CREATE TABLE IF NOT EXISTS query_cursors (id text PRIMARY KEY, result_id text REFERENCES query_results(id) ON DELETE CASCADE, offset_value integer NOT NULL);
