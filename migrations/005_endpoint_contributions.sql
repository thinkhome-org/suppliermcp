CREATE TABLE endpoint_checkpoints (
    interface text NOT NULL, domain text NOT NULL, endpoint text NOT NULL,
    started_at timestamptz NOT NULL, artifact_sha256 text NOT NULL,
    revision bigint NOT NULL, delta_to timestamptz,
    PRIMARY KEY(interface,domain,endpoint)
);
INSERT INTO endpoint_checkpoints
SELECT d.interface,d.domain,COALESCE((SELECT manifest->>'endpoint' FROM import_runs r WHERE r.revision=d.revision AND r.status='published' LIMIT 1),''),d.started_at,d.artifact_sha256,d.revision,d.delta_to FROM domain_checkpoints d;
ALTER TABLE observations ADD COLUMN value_key text NOT NULL DEFAULT '';
ALTER TABLE observations DROP CONSTRAINT observations_pkey;
ALTER TABLE observations ADD PRIMARY KEY(item_id,interface,endpoint,field,value_key);
ALTER TABLE current_offers ADD COLUMN endpoint text NOT NULL DEFAULT '';
UPDATE current_offers SET endpoint=COALESCE(data->'observations'->0->>'endpoint','');
ALTER TABLE current_offers DROP CONSTRAINT current_offers_pkey;
ALTER TABLE current_offers ADD PRIMARY KEY(item_id,interface,domain,endpoint);
ALTER TABLE source_schema ADD COLUMN endpoint text NOT NULL DEFAULT '';
ALTER TABLE source_schema DROP CONSTRAINT source_schema_pkey;
ALTER TABLE source_schema ADD PRIMARY KEY(interface,endpoint,kind,key);
ALTER TABLE relationships ADD COLUMN interface text NOT NULL DEFAULT '';
ALTER TABLE relationships ADD COLUMN endpoint text NOT NULL DEFAULT '';
UPDATE relationships SET interface=COALESCE(data->>'interface',''),endpoint=COALESCE(data->>'endpoint','');
ALTER TABLE relationships DROP CONSTRAINT relationships_pkey;
ALTER TABLE relationships ADD PRIMARY KEY(item_id,target_id,kind,interface,endpoint);
