from psycopg.conninfo import conninfo_to_dict

from suppliermcp.catalog import db
from suppliermcp.config import Settings


def test_app_and_queue_connections_preserve_security_options_and_bound_dead_tcp():
    settings = Settings(
        database_url="host=db dbname=fixture user=fixture password=fixture sslmode=verify-full options='-c search_path=trusted'"
    )
    params = conninfo_to_dict(db.connection_info(settings))
    assert params["sslmode"] == "verify-full"
    assert params["password"] == "fixture"
    assert params["options"].startswith("-c search_path=trusted ")
    assert "-c tcp_keepalives_idle=30" in params["options"]
    assert "-c tcp_keepalives_interval=10" in params["options"]
    assert "-c tcp_keepalives_count=3" in params["options"]
    assert "-c tcp_user_timeout=60000" in params["options"]
    assert {
        k: params[k]
        for k in [
            "keepalives",
            "keepalives_idle",
            "keepalives_interval",
            "keepalives_count",
            "tcp_user_timeout",
        ]
    } == {
        "keepalives": "1",
        "keepalives_idle": "30",
        "keepalives_interval": "10",
        "keepalives_count": "3",
        "tcp_user_timeout": "60000",
    }
    assert "statement_timeout" not in params["options"]
