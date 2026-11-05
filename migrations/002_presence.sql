CREATE TABLE IF NOT EXISTS source_presence (item_id text REFERENCES source_items(id) ON DELETE CASCADE, interface text NOT NULL, PRIMARY KEY(item_id,interface));
