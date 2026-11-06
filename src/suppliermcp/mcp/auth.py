import time

from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp.server.dependencies import get_access_token

from suppliermcp.access import AccessDenied, Identity, require_scope


class IdentityVerifier(JWTVerifier):
    def __init__(self, settings):
        if not all([settings.auth_public_key, settings.auth_issuer, settings.auth_audience]):
            raise ValueError("Token verification requires a public key, issuer and audience")
        super().__init__(
            public_key=settings.auth_public_key,
            issuer=settings.auth_issuer,
            audience=settings.auth_audience,
            algorithm="RS256",
        )
        self.clients = settings.auth_clients
        self.legacy_subjects = settings.auth_legacy_subjects

    async def load_access_token(self, token):
        access = await super().load_access_token(token)
        if not access or not access.expires_at or access.expires_at <= time.time():
            return None
        claims = access.claims
        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject:
            return None
        if "nbf" in claims and (
            type(claims["nbf"]) not in (int, float) or not claims["nbf"] <= time.time()
        ):
            return None
        if not {"client_id", "azp", "scope", "scp", "permissions"}.intersection(claims):
            if subject not in self.legacy_subjects:
                return None
            return access.model_copy(update={"scopes": ["catalog:read"]})

        client_id = claims.get("client_id", claims.get("azp"))
        if (
            not isinstance(client_id, str)
            or not client_id
            or claims.get("azp", client_id) != client_id
        ):
            return None
        registration = self.clients.get(client_id)
        if registration is None:
            return None
        granted = claims.get("scope", "")
        if not isinstance(granted, str):
            return None
        allowed = {"catalog:read"}
        if subject in registration.document_subjects:
            allowed.add("documents:read")
        return access.model_copy(update={"scopes": sorted(allowed.intersection(granted.split()))})


def verifier(settings):
    return IdentityVerifier(settings)


def identity_from_token(token) -> Identity:
    if token is None:
        raise AccessDenied(401)
    claims = token.claims
    return Identity(
        claims["iss"],
        claims["sub"],
        claims.get("client_id", claims.get("azp")),
        frozenset(token.scopes),
    )


def current_identity() -> Identity:
    return identity_from_token(get_access_token())


def principal() -> str:
    identity = current_identity()
    require_scope(identity, "catalog:read")
    return identity.principal
