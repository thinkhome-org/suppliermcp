ALTER TABLE catalog_values ADD COLUMN value_key text NOT NULL DEFAULT '';
ALTER TABLE catalog_values DROP CONSTRAINT catalog_values_pkey;
ALTER TABLE catalog_values ADD PRIMARY KEY(item_id,field,value_key);
