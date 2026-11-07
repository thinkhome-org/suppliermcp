from importlib.metadata import version

from fastmcp import FastMCP
from starlette.responses import JSONResponse

from suppliermcp.api import create_api
from suppliermcp.catalog.db import connect, require_projected_catalog
from suppliermcp.config import Settings

from . import resources, tools
from .auth import server_auth


def create_server(settings):
    server = FastMCP(
        "SupplierMCP",
        version=version("suppliermcp"),
        auth=server_auth(settings),
        mask_error_details=True,
        instructions=resources.HELP,
        strict_input_validation=True,
    )
    tools.register(server, settings)
    resources.register(server, settings)

    @server.custom_route("/health/live", methods=["GET"])
    async def live(request):
        return JSONResponse({"alive": True})

    @server.custom_route("/health/ready", methods=["GET"])
    def ready(request):
        try:
            with connect(settings) as conn:
                require_projected_catalog(conn)
            return JSONResponse({"ready": True})
        except Exception:
            return JSONResponse({"ready": False}, status_code=503)

    return server


def http_app(server, settings):
    app = server.http_app(
        path="/mcp",
        stateless_http=True,
        json_response=True,
        allowed_hosts=settings.allowed_hosts,
        allowed_origins=settings.allowed_origins,
    )
    app.mount("/v2", create_api(settings))
    return app


def main():
    import uvicorn

    settings = Settings.from_env()
    uvicorn.run(
        http_app(create_server(settings), settings), host="0.0.0.0", port=8000, log_level="warning"
    )


if __name__ == "__main__":
    main()
