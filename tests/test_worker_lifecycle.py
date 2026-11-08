import threading
from concurrent.futures import ThreadPoolExecutor

import psycopg
import pytest

from suppliermcp.sync.lifecycle import abortable_job, check_abort, register_connection


class Context:
    def __init__(self):
        self.abort = threading.Event()

    def should_abort(self):
        return self.abort.is_set()


def test_cooperative_abort_unwinds_and_resets_context():
    context = Context()
    cleaned = []

    @abortable_job
    def job():
        try:
            context.abort.set()
            check_abort()
            pytest.fail("continued after abort")
        finally:
            cleaned.append(True)

    from procrastinate.exceptions import JobAborted

    with pytest.raises(JobAborted):
        job(context=context)
    assert cleaned == [True]
    check_abort()
    assert job.__name__ == "job"


def test_no_context_creates_no_monitor_and_preserves_result(monkeypatch):
    monkeypatch.setattr(threading.Thread, "start", lambda self: pytest.fail("monitor started"))

    @abortable_job
    def job(value):
        assert register_connection(value) is value
        check_abort()
        return value

    assert job(42, context=None) == 42


def test_watcher_cancels_blocked_query_repeatedly_and_joins():
    context = Context()
    started = threading.Event()
    unblocked = threading.Event()
    monitor = []

    class Connection:
        calls = 0

        def cancel_safe(self, *, timeout):
            assert timeout == 1
            monitor.append(threading.current_thread())
            self.calls += 1
            if self.calls >= 2:
                unblocked.set()

    conn = Connection()

    @abortable_job
    def job():
        assert register_connection(conn) is conn
        started.set()
        assert unblocked.wait(3), "query was never cancelled"
        raise psycopg.errors.QueryCanceled("cancelled")

    from procrastinate.exceptions import JobAborted

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(job, context=context)
        assert started.wait(1)
        context.abort.set()
        with pytest.raises(JobAborted):
            future.result(timeout=4)
    assert conn.calls >= 2
    assert all(not thread.is_alive() for thread in monitor)
    check_abort()


def test_closed_connection_race_does_not_stop_other_cancellations():
    context = Context()
    released = threading.Event()

    class ClosedConnection:
        def cancel_safe(self, *, timeout):
            raise psycopg.OperationalError("connection is closed")

    class Connection:
        def cancel_safe(self, *, timeout):
            released.set()

    @abortable_job
    def job():
        register_connection(ClosedConnection())
        register_connection(Connection())
        context.abort.set()
        assert released.wait(2)
        check_abort()

    from procrastinate.exceptions import JobAborted

    with pytest.raises(JobAborted):
        job(context=context)


def test_concurrent_job_contexts_are_isolated():
    aborted = Context()
    healthy = Context()
    barrier = threading.Barrier(2)

    @abortable_job
    def job(abort):
        barrier.wait(timeout=2)
        if abort:
            aborted.abort.set()
        check_abort()
        return "healthy"

    from procrastinate.exceptions import JobAborted

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(job, True, context=aborted)
        second = executor.submit(job, False, context=healthy)
        with pytest.raises(JobAborted):
            first.result(timeout=3)
        assert second.result(timeout=3) == "healthy"


def test_wrapped_query_cancellation_remains_an_abort():
    from procrastinate.exceptions import JobAborted

    from suppliermcp.catalog.contracts import CatalogError

    context = Context()

    @abortable_job
    def job():
        context.abort.set()
        raise CatalogError("invalid_export")

    with pytest.raises(JobAborted):
        job(context=context)


def test_refresh_interruption_does_not_mark_valid_offers_failed(monkeypatch):
    from procrastinate.exceptions import JobAborted

    from suppliermcp.sync import jobs

    context = Context()

    class Connection:
        def execute(self, *args):
            pytest.fail("shutdown must not mark offers or update source state")

    class Adapter:
        interface = "mega"

        def fetch(self, domain, codes):
            context.abort.set()
            check_abort()

    @abortable_job
    def job():
        jobs._run_refresh(Connection(), Adapter(), "catalog", None, None, "base")

    with pytest.raises(JobAborted):
        job(context=context)


def test_procrastinate_positional_job_context_is_consumed():
    from procrastinate.job_context import JobContext

    context = JobContext(app=None, job=None, start_timestamp=0, abort_reason=lambda: None)

    @abortable_job
    def job(value):
        check_abort()
        return value

    assert job(context, value=42) == 42
