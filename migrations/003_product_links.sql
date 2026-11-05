CREATE TABLE IF NOT EXISTS product_links (left_id text REFERENCES source_items(id) ON DELETE CASCADE, right_id text REFERENCES source_items(id) ON DELETE CASCADE, evidence jsonb NOT NULL, blocked boolean NOT NULL DEFAULT false, PRIMARY KEY(left_id,right_id));
CREATE INDEX IF NOT EXISTS source_items_sku ON source_items ((data->>'supplier'),(data->>'sku'));
CREATE INDEX IF NOT EXISTS source_items_ean ON source_items ((data->>'ean'));
CREATE INDEX IF NOT EXISTS source_items_mpn ON source_items ((data->>'mpn'));
