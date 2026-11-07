CREATE TABLE ed_commodity_cycles (
    baseline_run_id uuid PRIMARY KEY REFERENCES import_runs(id) ON DELETE CASCADE,
    finished boolean NOT NULL DEFAULT false
);
CREATE UNIQUE INDEX ed_one_open_commodity_cycle ON ed_commodity_cycles(finished) WHERE NOT finished;
CREATE TABLE ed_commodity_parts (
    baseline_run_id uuid NOT NULL REFERENCES ed_commodity_cycles(baseline_run_id) ON DELETE CASCADE,
    code text NOT NULL CHECK (code <> '' AND code = btrim(code)),
    chunk_run_id uuid UNIQUE REFERENCES import_runs(id),
    empty boolean,
    PRIMARY KEY (baseline_run_id, code),
    CHECK ((chunk_run_id IS NULL) = (empty IS NULL))
);
