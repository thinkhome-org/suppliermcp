from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp.server.dependencies import get_access_token

from suppliermcp.catalog.contracts import CatalogError


class IdentityVerifier(JWTVerifier):
    async def verify_token(self, token):
        access = await super().verify_token(token)
        if not access or not access.claims.get("sub") or not access.expires_at:
            return None
        return access


def verifier(settings):
    if not settings.auth_public_key:
        raise ValueError("SUPPLIERMCP_AUTH_PUBLIC_KEY is required")
    return IdentityVerifier(
        public_key=settings.auth_public_key,
        issuer=settings.auth_issuer,
        audience=settings.auth_audience,
        algorithm="RS256",
    )


def principal():
    token = get_access_token()
    if not token or not token.claims.get("sub"):
        raise CatalogError("unauthorized")
    return str(token.claims["iss"]) + ":" + str(token.claims["sub"])
