"""Maintenance entry point; never exposed as an agent tool."""

import argparse

from suppliermcp.catalog.db import connect, migrate
from suppliermcp.config import Settings
from suppliermcp.sync.jobs import create_app
from suppliermcp.sync.publish import publish


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["migrate", "run", "accept-import", "rebuild-index"])
    parser.add_argument("run_id", nargs="?")
    parser.add_argument("--reason")
    args = parser.parse_args()
    settings = Settings.from_env()
    app = create_app(settings)
    if args.command == "run":
        with app.open():
            app.run_worker()
        return
    with connect(settings) as conn:
        if args.command == "migrate":
            migrate(conn)
            if not conn.execute("SELECT to_regclass('procrastinate_jobs')").fetchone()[0]:
                with app.open():
                    app.schema_manager.apply_schema()
        elif args.command == "rebuild-index":
            from suppliermcp.search.index import configured_client, rebuild_index

            client = configured_client(settings)
            try:
                rebuild_index(conn, client)
            finally:
                client.http.close()
        else:
            if not args.run_id or not args.reason:
                parser.error("accept-import requires RUN_ID and --reason")
            publish(conn, args.run_id, accept_reason=args.reason)


if __name__ == "__main__":
    main()
