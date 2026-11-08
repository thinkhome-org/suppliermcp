#!/usr/bin/env python3
"""Real Docker acceptance: SUPPLIERMCP_SMOKE_IMAGE=<exact image> python scripts/worker_shutdown_smoke.py.

Uses only a dedicated disposable database and fixture credentials. No production env is forwarded.
"""

import ipaddress
import os
import subprocess
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSTGRES = "postgres@sha256:10a5c69a83035ab5239f5620d708520e8b28f5aa1f2b20143e6024532edadfb5"


def docker(*args, check=True):
    return subprocess.run(
        ["docker", *args], check=check, text=True, capture_output=True, timeout=120
    ).stdout.strip()


def wait_for(predicate, seconds=15):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.2)
    raise AssertionError("Fixture condition did not become true within deadline")


def main():
    image = os.environ["SUPPLIERMCP_SMOKE_IMAGE"]
    prefix = "shutdown-" + uuid.uuid4().hex[:12]
    network, db = prefix + "-net", prefix + "-db"
    workers = []
    slow_http = prefix + "-http"
    dsn = f"postgresql://fixture:fixture@{db}/fixture"
    common = [
        "--network",
        network,
        "-e",
        "SUPPLIERMCP_TEST_DSN=" + dsn,
        "-e",
        "SUPPLIERMCP_SLOW_HTTP_URL=http://" + slow_http + ":8080/fixture",
        "-v",
        str(ROOT / "tests/fixtures/worker_shutdown_job.py") + ":/fixture.py:ro",
    ]

    def sql(query):
        return docker("exec", db, "psql", "-U", "fixture", "-d", "fixture", "-Atc", query)

    def fixture(*args):
        return docker("run", "--rm", *common, image, "python", "/fixture.py", *args)

    def start():
        name = prefix + "-worker-" + str(len(workers))
        workers.append(name)
        docker("run", "-d", "--name", name, *common, image, "python", "/fixture.py", "worker")
        return name

    def active(token, waiting=False, http=False):
        extra = " AND wait_event_type='Lock'" if waiting else " AND query LIKE 'COPY%'"
        if http:
            extra = ""
        return sql(
            "SELECT pid FROM pg_stat_activity WHERE application_name='shutdown:"
            + token
            + "'"
            + extra
        )

    def sessions_at(address):
        address = str(ipaddress.IPv4Address(address))
        return sql(f"SELECT count(*) FROM pg_stat_activity WHERE client_addr='{address}'")

    def released(pid, address):
        assert sql(f"SELECT count(*) FROM pg_stat_activity WHERE pid={pid}") == "0"
        assert sessions_at(address) == "0", "Old worker still owns database sessions"
        assert sql("SELECT pg_try_advisory_xact_lock(91002)") == "t"

    try:
        docker("network", "create", network)
        docker(
            "run",
            "-d",
            "--name",
            db,
            "--network",
            network,
            "-e",
            "POSTGRES_USER=fixture",
            "-e",
            "POSTGRES_PASSWORD=fixture",
            "-e",
            "POSTGRES_DB=fixture",
            POSTGRES,
        )
        wait_for(
            lambda: docker(
                "exec",
                db,
                "pg_isready",
                "-h",
                "127.0.0.1",
                "-U",
                "fixture",
                "-d",
                "fixture",
                check=False,
            ).endswith("accepting connections"),
            40,
        )
        print(fixture("init"))
        workers.append(slow_http)
        docker(
            "run", "-d", "--name", slow_http, *common, image, "python", "/fixture.py", "http-server"
        )
        wait_for(lambda: "HTTP_READY" in docker("logs", slow_http))
        for index, token in enumerate(("graceful1", "graceful2", "lockwait", "http", "blackhole")):
            blocker = None
            if token == "lockwait":
                blocker = prefix + "-blocker"
                workers.append(blocker)
                docker(
                    "run", "-d", "--name", blocker, *common, image, "python", "/fixture.py", "block"
                )
                wait_for(
                    lambda: (
                        sql(
                            "SELECT count(*) FROM pg_locks WHERE locktype='advisory' AND objid=91004 AND granted"
                        )
                        == "1"
                    )
                )
            fixture("enqueue", token, "http" if token == "http" else "wait" if blocker else "copy")
            worker = start()
            wait_for(
                lambda token=token, blocker=blocker: active(
                    token, waiting=bool(blocker), http=token == "http"
                )
            )
            pid = int(active(token, waiting=bool(blocker), http=token == "http"))
            address = docker(
                "inspect",
                "--format",
                "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}",
                worker,
            )
            if token == "http":
                wait_for(lambda: "HTTP_STALL_ENTERED" in docker("logs", slow_http))
            if token == "graceful1":
                time.sleep(35)
                assert int(active(token)) == pid, "Healthy COPY was timed out"
            if token == "blackhole":
                docker("network", "disconnect", network, worker)
                docker("kill", worker)
                wait_for(
                    lambda pid=pid: sessions_at(address) == "0",
                    100,
                )
            else:
                started = time.monotonic()
                docker("kill", "--signal", "TERM", worker)
                assert docker("wait", worker) == "0"
                assert time.monotonic() - started < (85 if token == "http" else 15)
            released(pid, address)
            assert sql("SELECT count(*) FROM shutdown_markers") == str(index)
            if blocker:
                docker("rm", "-f", blocker)
            if token != "blackhole":
                sql(f"UPDATE shutdown_control SET ready=true WHERE token='{token}'")
                worker = start()
                wait_for(
                    lambda token=token: (
                        sql(f"SELECT count(*) FROM shutdown_markers WHERE token='{token}'") == "1"
                    )
                )
                docker("kill", "--signal", "TERM", worker)
                assert docker("wait", worker) == "0"
        # A fresh job after hard loss must be able to publish, without terminating a backend.
        fixture("enqueue", "after-harddeath", "copy")
        sql("UPDATE shutdown_control SET ready=true WHERE token='after-harddeath'")
        worker = start()
        wait_for(
            lambda: (
                sql("SELECT count(*) FROM shutdown_markers WHERE token='after-harddeath'") == "1"
            )
        )
        docker("kill", "--signal", "TERM", worker)
        assert docker("wait", worker) == "0"
        print(
            "PASS: healthy COPY, graceful retry/commit cycles, blocked SQL cancellation, stalled HTTP cancellation, and blackhole lock release"
        )
    except BaseException:
        for name in workers + [db]:
            print(docker("logs", "--tail", "35", name, check=False)[-6000:], flush=True)
        raise
    finally:
        for name in workers + [db]:
            docker("rm", "-fv", name, check=False)
        docker("network", "rm", network, check=False)


if __name__ == "__main__":
    main()
