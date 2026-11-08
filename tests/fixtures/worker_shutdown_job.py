"""Supplier-free worker fixture, also runnable inside the exact release image."""

import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import procrastinate
from pydantic import SecretStr

from suppliermcp.catalog.db import connect, connection_info
from suppliermcp.config import Settings
from suppliermcp.suppliers.transport import SupplierTransport
from suppliermcp.sync.lifecycle import abortable_job, check_abort

settings = Settings(database_url=SecretStr(os.environ["SUPPLIERMCP_TEST_DSN"]))
app = procrastinate.App(
    connector=procrastinate.PsycopgConnector(conninfo=connection_info(settings))
)


@app.task(
    name="shutdown.fixture",
    queue="shutdown-test",
    pass_context=True,
    retry=procrastinate.RetryStrategy(max_attempts=3, wait=1),
)
@abortable_job
def fixture(token, mode="copy"):
    with connect(settings) as conn, connect(settings) as control:
        conn.execute("SELECT set_config('application_name', %s, false)", ("shutdown:" + token,))
        with conn.transaction():
            conn.execute("SELECT pg_advisory_xact_lock(91002)")
            if (
                mode == "http"
                and not control.execute(
                    "SELECT ready FROM shutdown_control WHERE token=%s", (token,)
                ).fetchone()[0]
            ):
                conn.execute("INSERT INTO shutdown_markers VALUES (%s)", (token,))

                def forward(request):
                    assert str(request.url) == "https://8.8.8.8/fixture"
                    with httpx.stream(
                        "GET",
                        os.environ["SUPPLIERMCP_SLOW_HTTP_URL"],
                        timeout=httpx.Timeout(**request.extensions["timeout"]),
                        trust_env=False,
                    ) as response:
                        return httpx.Response(response.status_code, content=response.read())

                class Store:
                    def save(self, chunks, manifest):
                        return b"".join(chunks)

                with httpx.Client(transport=httpx.MockTransport(forward)) as client:
                    transport = SupplierTransport(
                        {"fixture.invalid"},
                        {"download"},
                        client=client,
                        resolver=lambda host: ["8.8.8.8"],
                        download_timeout=900,
                    )
                    transport.download("https://fixture.invalid/fixture", Store(), None)
            if mode == "wait":
                conn.execute("SELECT pg_advisory_xact_lock(91004)")
            with conn.cursor().copy("COPY shutdown_markers (token) FROM STDIN") as copy:
                copy.write_row((token,))
                while not control.execute(
                    "SELECT ready FROM shutdown_control WHERE token=%s", (token,)
                ).fetchone()[0]:
                    check_abort()
                    time.sleep(0.05)


def initialize():
    with connect(settings) as conn:
        missing = conn.execute("SELECT to_regclass('procrastinate_jobs') IS NULL").fetchone()[0]
    if missing:
        with app.open():
            app.schema_manager.apply_schema()
    with connect(settings) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS shutdown_control (token text PRIMARY KEY, ready boolean NOT NULL)"
        )
        conn.execute("CREATE TABLE IF NOT EXISTS shutdown_markers (token text PRIMARY KEY)")
        actual = {
            key: conn.execute("SHOW " + key).fetchone()[0]
            for key in (
                "tcp_keepalives_idle",
                "tcp_keepalives_interval",
                "tcp_keepalives_count",
                "tcp_user_timeout",
            )
        }
        raw = dict(
            conn.execute(
                "SELECT name, setting FROM pg_settings WHERE name = ANY(%s)", (list(actual),)
            ).fetchall()
        )
        assert raw == dict(
            tcp_keepalives_idle="30",
            tcp_keepalives_interval="10",
            tcp_keepalives_count="3",
            tcp_user_timeout="60000",
        ), raw
        print(actual, flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "init":
        initialize()
    elif sys.argv[1] == "enqueue":
        token, mode = sys.argv[2:4]
        with connect(settings) as conn:
            conn.execute("INSERT INTO shutdown_control VALUES (%s, false)", (token,))
        with app.open():
            fixture.defer(token=token, mode=mode)
    elif sys.argv[1] == "http-server":

        class SlowHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                print("HTTP_STALL_ENTERED", flush=True)
                time.sleep(120)
                self.send_response(200)
                self.end_headers()

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("0.0.0.0", 8080), SlowHandler)
        print("HTTP_READY", flush=True)
        server.serve_forever()
    elif sys.argv[1] == "block":
        with connect(settings) as conn:
            conn.execute("SELECT pg_advisory_lock(91004)")
            conn.execute("SELECT pg_sleep(120)")
    elif sys.argv[1] == "worker":
        app.run_worker(
            queues=["shutdown-test"],
            shutdown_graceful_timeout=0.2,
            fetch_job_polling_interval=0.1,
            abort_job_polling_interval=0.1,
        )
