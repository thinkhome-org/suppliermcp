from fastmcp import FastMCP
from starlette.responses import JSONResponse

from suppliermcp.catalog.db import connect
from suppliermcp.config import Settings

from . import resources, tools
from .auth import verifier


def create_server(settings):
    server = FastMCP(
        "SupplierMCP",
        version="1.0.0",
        auth=verifier(settings),
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
    async def ready(request):
        try:
            with connect(settings) as conn:
                conn.execute("SELECT 1 FROM source_items LIMIT 1")
            return JSONResponse({"ready": True})
        except Exception:
            return JSONResponse({"ready": False}, status_code=503)

    return server


def http_app(server, settings):
    return server.http_app(
        path="/mcp",
        stateless_http=True,
        json_response=True,
        allowed_hosts=settings.allowed_hosts,
        allowed_origins=settings.allowed_origins,
    )


def main():
    import uvicorn

    settings = Settings.from_env()
    uvicorn.run(
        http_app(create_server(settings), settings), host="0.0.0.0", port=8000, log_level="warning"
    )


if __name__ == "__main__":
    main()
