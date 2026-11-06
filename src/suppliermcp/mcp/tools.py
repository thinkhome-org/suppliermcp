from functools import wraps
from inspect import signature

from fastmcp.exceptions import ToolError

from suppliermcp.catalog.contracts import CatalogError
from suppliermcp.service import CATALOG_OPERATIONS, CatalogService
from suppliermcp.suppliers.reads import OperationReader

from .auth import current_identity


def register(server, settings):
    reader = OperationReader(settings)
    read = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }

    def register_method(name):
        method = getattr(CatalogService, name)

        @wraps(method)
        async def call(**kwargs):
            service = CatalogService(settings, current_identity(), reader)
            try:
                return await method(service, **kwargs)
            except CatalogError as error:
                raise ToolError(error.code) from None

        # FastMCP publishes the shared method's typed arguments, except its bound service.
        params = signature(method)
        call.__signature__ = params.replace(parameters=list(params.parameters.values())[1:])
        annotations = read | {
            "idempotentHint": name != "compare_offers",
            "openWorldHint": name == "read_operation",
        }
        server.tool(annotations=annotations)(call)

    for name in (*CATALOG_OPERATIONS, "list_operations", "read_operation"):
        register_method(name)
