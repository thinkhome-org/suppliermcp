CREATE TABLE query_result_rows (
    result_id text NOT NULL REFERENCES query_results(id) ON DELETE CASCADE,
    ordinal bigint NOT NULL,
    data jsonb NOT NULL,
    PRIMARY KEY(result_id, ordinal)
);
