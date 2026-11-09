# Worker shutdown and recovery

SupDB 2.0.2 fixes [#35](https://github.com/thinkhome-org/suppliermcp/issues/35): stopping a worker must not leave a COPY transaction or advisory lock blocking publication/indexing. The fix is in [PR #37](https://github.com/thinkhome-org/suppliermcp/pull/37). [Deployment evidence](releases/2.0.2/deployment.json) records the accepted image and observed timings.

## What happens on stop

The worker allows 30 seconds for jobs to finish. Procrastinate then requests cooperative cancellation. A synchronous Python job is a thread, so the application must actually observe that request: a job-local monitor cancels only its own registered PostgreSQL connections, including active COPY and advisory-lock waits. Connection context managers perform rollback and close; the monitor never closes another thread's connection. Parsing, download, publication and index loops check cancellation at safe points. An aborted refresh does not replace valid offers with a fabricated supplier failure.

Worker supplier HTTP requests have a read-inactivity timeout of at most 60 seconds, with cancellation checks between unbuffered chunks and before retries/redirects. This is **not** a total download-duration limit. Ordinary calls outside a worker retain their configured timeouts. The download must keep sending data; a silent server cannot hold shutdown indefinitely. Index HTTP requests retain their existing bounded timeout.

Every application and queue connection configures both client and PostgreSQL server TCP keepalives: idle 30 seconds, interval 10 seconds, count 3, TCP user timeout 60,000 ms. These detect a dead network peer, including a worker lost without a clean socket close. They do not cancel healthy long SQL/COPY merely because its duration exceeds 30 seconds. No global statement timeout was added.

The Compose worker has a five-minute stop grace period. Use ordinary Portainer Stop/Start or stack update; do not shorten Docker's grace period below the measured cancellation path. A silent HTTP request took about 63 seconds to unwind in the exact-image test. Network blackhole cleanup took about 61 seconds on the tested VM; these are observations, not a hard real-time guarantee under every host/IO failure.

## Restart safely

Keep PostgreSQL, Typesense and artifact volumes. Do not clear the queue, delete the catalog or run `down -v`. Durable jobs and source checkpoints permit retry; incomplete publication rolls back and committed batches remain valid. The outbox resumes after restart. A nonzero backlog can mean normal processing: check that it decreases and inspect job/lock ownership before declaring an index blocked.

Never terminate every PostgreSQL backend as a recovery strategy. An exceptional legacy cleanup requires independent proof of ownership (old worker network address, client port, backend start time and exact operation). New 2.0.2 stop/restart acceptance explicitly forbids manual backend termination. The transition from 2.0.1 required none.

## Reproduce without supplier credentials

Run the committed `scripts/worker_shutdown_smoke.py` against the exact application image on a Docker host, as done in CI. Set `SUPPLIERMCP_SMOKE_IMAGE` to the verified digest before invoking it; the script has no command-line parser. It creates isolated, uniquely named PostgreSQL/network/test containers; it does not use production volumes or supplier credentials. The fixture runs against installed application code, with no source replacement.

The test covers a healthy COPY held beyond the keepalive idle threshold, two stop/retry/commit cycles, blocked SQL cancellation, stalled HTTP cancellation, and network disconnection before hard worker death. It checks every connection from the worker's network address, advisory-lock release, rollback and exactly one subsequent commit. Stage additionally stops the actual application worker while its real index task waits for the publication lock; production additionally checks its own worker and index resumption.

See [operations](operations.md) for backup/restore and index rebuild procedures. This patch changes no database schema and requires no fresh catalog import.

## Primary references

- [Procrastinate shutdown](https://github.com/procrastinate-org/procrastinate/blob/main/docs/howto/advanced/shutdown.md?plain=true): a synchronous task must cooperate with abort requests.
- [PostgreSQL connection settings](https://www.postgresql.org/docs/18/runtime-config-connection.html): TCP keepalive and user-timeout semantics.
- [HTTPX timeouts](https://www.python-httpx.org/advanced/timeouts/): read timeout measures waiting for a network chunk.

## Throughput is separate from a stranded worker

After the production restart, a healthy eD PUBLIC catalog refresh completed in about 39 minutes. The index then resumed and its outbox decreased. A profiled real batch processed 200 products/events in 16.092 seconds, including ordinary lock waiting and profiling overhead. Preparing documents accounted for 10.820 seconds; `get_products` accounted for 9.039 seconds and decoded roughly 126,000 JSON records. This is one diagnostic sample, not a latency percentile or an import-duration guarantee.

The existing index path reconstructs complete product evidence before building searchable text. A dedicated index projection could reduce that cost, but must preserve observation values, mapped values, relationship names and dictionary labels. This patch does not replace that projection or discard evidence to obtain a faster result. A slowly decreasing outbox should be distinguished from a dead worker holding a publication lock.
