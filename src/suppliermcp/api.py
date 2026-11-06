"""Versioned HTTP adapter for the shared read service."""

from importlib.metadata import version
from inspect import Parameter, signature
from typing import Annotated

from fastapi import Depends, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import create_model
from starlette.responses import JSONResponse

from suppliermcp.access import AccessDenied
from suppliermcp.catalog.contracts import CatalogError, Model
from suppliermcp.mcp.auth import identity_from_token, verifier
from suppliermcp.service import CATALOG_OPERATIONS, CatalogService
from suppliermcp.suppliers.reads import OperationReader, ReadResult


def create_api(settings):
    app = FastAPI(title="SupplierMCP read API", version=version("suppliermcp"))
    reader = OperationReader(settings)
    tokens = verifier(settings)
    bearer = HTTPBearer(auto_error=False)

    async def get_service(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    ):
        token = await tokens.verify_token(credentials.credentials) if credentials else None
        return CatalogService(settings, identity_from_token(token), reader)

    service_parameter = Annotated[CatalogService, Depends(get_service)]

    @app.exception_handler(CatalogError)
    async def error_response(request: Request, error: CatalogError):
        status = error.status_code if isinstance(error, AccessDenied) else 400
        headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
        return JSONResponse({"error": error.as_dict()}, status_code=status, headers=headers)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, error: RequestValidationError):
        # Validation details can echo customer document contents.
        return JSONResponse({"error": CatalogError("invalid_arguments").as_dict()}, status_code=422)

    @app.get("/operations")
    async def list_operations(service: service_parameter, offset: Annotated[int, Query(ge=0)] = 0):
        return await service.list_operations(offset)

    @app.post("/operations/{operation_id}/read")
    async def read_operation(
        operation_id: str, arguments: dict, service: service_parameter
    ) -> ReadResult:
        return await service.read_operation(operation_id, arguments)

    def add_catalog_route(name):
        method = getattr(CatalogService, name)
        params = signature(method)
        fields = {
            p.name: (p.annotation, ... if p.default is Parameter.empty else p.default)
            for p in list(params.parameters.values())[1:]
        }
        body = create_model(name + "_request", __base__=Model, **fields)

        async def endpoint(arguments: body, service: service_parameter):
            return await method(service, **dict(arguments))

        app.add_api_route(
            "/catalog/" + name,
            endpoint,
            methods=["POST"],
            name=name,
            response_model=params.return_annotation,
            description=method.__doc__,
        )

    for name in CATALOG_OPERATIONS:
        add_catalog_route(name)
    return app
