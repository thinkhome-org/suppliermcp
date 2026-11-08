"""Cooperative cancellation for synchronous Procrastinate jobs."""

import threading
from contextvars import ContextVar
from functools import wraps

import psycopg
from procrastinate.exceptions import JobAborted
from procrastinate.job_context import JobContext


class _JobScope:
    def __init__(self, context: JobContext):
        self.context = context
        self.connections = []
        self.lock = threading.Lock()
        self.stopped = threading.Event()

    def monitor(self):
        while not self.stopped.wait(0.1):
            if not self.context.should_abort():
                continue
            with self.lock:
                connections = list(self.connections)
            for connection in connections:
                if self.stopped.is_set():
                    return
                try:
                    # Cancellation is thread-safe; closing here would race job cleanup.
                    connection.cancel_safe(timeout=1)
                except psycopg.Error:
                    pass  # Connections may already have closed while the job unwinds.


_scope: ContextVar[_JobScope | None] = ContextVar("sync_job_scope", default=None)


def in_job():
    return _scope.get() is not None


def check_abort():
    scope = _scope.get()
    if scope is not None and scope.context.should_abort():
        raise JobAborted()


def register_connection(connection):
    scope = _scope.get()
    if scope is not None:
        with scope.lock:
            scope.connections.append(connection)
    return connection


def abortable_job(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        context = kwargs.pop("context", None)
        if args and isinstance(args[0], JobContext):
            context, args = args[0], args[1:]
        if context is None:
            return func(*args, **kwargs)
        scope = _JobScope(context)
        token = _scope.set(scope)
        monitor = threading.Thread(target=scope.monitor, name="sync-job-abort")
        try:
            check_abort()
            monitor.start()
            try:
                result = func(*args, **kwargs)
            except Exception:
                # Parsers may wrap a cancelled query; shutdown is still an abort.
                check_abort()
                raise
            check_abort()
            return result
        finally:
            scope.stopped.set()
            if monitor.ident is not None:
                monitor.join()
            _scope.reset(token)

    return wrapped
