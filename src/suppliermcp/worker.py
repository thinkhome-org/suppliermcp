"""Maintenance entry point; never exposed as an agent tool."""

import argparse

from suppliermcp.catalog.db import connect, migrate
from suppliermcp.config import Settings
from suppliermcp.sync.jobs import create_app
from suppliermcp.sync.publish import publish


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command", choices=["migrate", "run", "refresh", "accept-import", "rebuild-index"]
    )
    parser.add_argument("run_id", nargs="?")
    parser.add_argument("--reason")
    parser.add_argument(
        "--domain", default="catalog", choices=["catalog", "price", "stock", "schema"]
    )
    parser.add_argument("--endpoint")
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
        elif args.command == "refresh":
            from suppliermcp.sync.jobs import build_adapters, run_export_refresh, run_refresh

            adapters = build_adapters(settings)
            if args.run_id not in adapters:
                parser.error("refresh requires a configured interface")
            adapter = adapters[args.run_id]
            if args.endpoint:
                if args.run_id != "mega":
                    parser.error("explicit endpoints are supported only for mega")
                run_export_refresh(conn, adapter, args.endpoint)
            else:
                run_refresh(conn, adapter, args.domain)
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
