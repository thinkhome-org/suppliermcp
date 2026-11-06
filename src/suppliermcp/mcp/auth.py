import time

import jwt
from fastmcp.server.auth.auth import RemoteAuthProvider, TokenVerifier
from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp.server.dependencies import get_access_token
from pydantic import AnyHttpUrl

from suppliermcp.access import AccessDenied, Identity, require_scope


class IdentityVerifier(JWTVerifier):
    def __init__(self, settings, *, jwks_uri=None):
        if not all(
            [jwks_uri or settings.auth_public_key, settings.auth_issuer, settings.auth_audience]
        ):
            raise ValueError("Token verification requires a public key, issuer and audience")
        super().__init__(
            public_key=None if jwks_uri else settings.auth_public_key,
            jwks_uri=jwks_uri,
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


class IssuerVerifier(TokenVerifier):
    """Select from configured issuers, then verify signature, audience and grants."""

    def __init__(self, issuers):
        super().__init__()
        self.issuers = issuers

    async def verify_token(self, token):
        try:
            issuer = jwt.decode(token, options={"verify_signature": False}).get("iss")
        except jwt.PyJWTError:
            return None
        verifier = self.issuers.get(issuer) if isinstance(issuer, str) else None
        return await verifier.verify_token(token) if verifier else None


def verifier(settings):
    static = IdentityVerifier(settings)
    if not (settings.oauth_issuer or settings.oauth_public_url):
        return static
    issuer = settings.oauth_issuer.rstrip("/")
    public = settings.oauth_public_url.rstrip("/")
    for value in (issuer, public):
        url = AnyHttpUrl(value)
        if url.scheme != "https" or url.username or url.password or url.query or url.fragment:
            raise ValueError("OAuth requires HTTPS issuer and resource URLs")
    if issuer == settings.auth_issuer:
        raise ValueError("OAuth and static issuers must be distinct")
    oauth = settings.model_copy(
        update={
            "auth_issuer": issuer,
            "auth_audience": public + "/mcp",
            "auth_legacy_subjects": set(),
        }
    )
    return IssuerVerifier(
        {
            settings.auth_issuer: static,
            issuer: IdentityVerifier(oauth, jwks_uri=issuer + "/protocol/openid-connect/certs"),
        }
    )


def server_auth(settings):
    tokens = verifier(settings)
    if not settings.oauth_issuer:
        return tokens
    return RemoteAuthProvider(
        token_verifier=tokens,
        authorization_servers=[AnyHttpUrl(settings.oauth_issuer)],
        base_url=settings.oauth_public_url,
        scopes_supported=["catalog:read", "documents:read"],
        resource_name="SupplierMCP",
    )


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
