"""Real Procrastinate shutdown against the integration PostgreSQL service."""

import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import psycopg

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/worker_shutdown_job.py"


def test_worker_cancel_blocked_query_rolls_back():
    dsn = os.getenv("SUPPLIERMCP_TEST_DSN", "postgresql://test:test@localhost:55439/test")
    env = {**os.environ, "SUPPLIERMCP_TEST_DSN": dsn}
    token = uuid.uuid4().hex
    process = None
    subprocess.run([sys.executable, str(FIXTURE), "init"], env=env, check=True, timeout=15)
    with psycopg.connect(dsn, autocommit=True) as observer:
        observer.execute(
            "CREATE TABLE IF NOT EXISTS shutdown_control (token text PRIMARY KEY, ready boolean NOT NULL)"
        )
        observer.execute("CREATE TABLE IF NOT EXISTS shutdown_markers (token text PRIMARY KEY)")
        # Keep the query inside the job blocked; cancellation must interrupt libpq.
        observer.execute("SELECT pg_advisory_lock(91004)")
        try:
            subprocess.run(
                [sys.executable, str(FIXTURE), "enqueue", token, "wait"],
                env=env,
                check=True,
                timeout=15,
            )
            process = subprocess.Popen([sys.executable, str(FIXTURE), "worker"], env=env)
            deadline = time.monotonic() + 15
            pid = None
            while time.monotonic() < deadline:
                row = observer.execute(
                    "SELECT pid FROM pg_stat_activity WHERE application_name=%s AND wait_event_type='Lock'",
                    ("shutdown:" + token,),
                ).fetchone()
                if row:
                    pid = row[0]
                    break
                assert process.poll() is None, "Worker exited before executing job"
                time.sleep(0.1)
            assert pid is not None, "Job never reached blocked database query"
            process.terminate()
            assert process.wait(timeout=15) == 0
            assert (
                observer.execute(
                    "SELECT count(*) FROM pg_stat_activity WHERE pid=%s", (pid,)
                ).fetchone()[0]
                == 0
            )
            assert observer.execute("SELECT pg_try_advisory_xact_lock(91002)").fetchone()[0]
            assert (
                observer.execute(
                    "SELECT count(*) FROM shutdown_markers WHERE token=%s", (token,)
                ).fetchone()[0]
                == 0
            )
        finally:
            if process is not None and process.poll() is None:
                process.kill()
                process.wait(timeout=10)
            observer.execute("SELECT pg_advisory_unlock(91004)")
            observer.execute(
                "DELETE FROM procrastinate_jobs WHERE task_name='shutdown.fixture' AND args->>'token'=%s",
                (token,),
            )
            observer.execute("DELETE FROM shutdown_control WHERE token=%s", (token,))
            observer.execute("DELETE FROM shutdown_markers WHERE token=%s", (token,))
