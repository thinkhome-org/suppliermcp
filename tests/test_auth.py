import time

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from suppliermcp.config import Settings
from suppliermcp.mcp.auth import verifier


def keys():
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = (
        private.public_key()
        .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        .decode()
    )
    return private, public


async def test_verifier_requires_identity_and_expiration():
    private, public = keys()
    auth = verifier(Settings(auth_public_key=public, auth_legacy_subjects=["alice"]))
    claims = {"sub": "alice", "iss": "suppliermcp", "aud": "suppliermcp", "exp": time.time() + 600}
    assert await auth.verify_token(jwt.encode(claims, private, algorithm="RS256"))
    for patch in [
        {"exp": time.time() - 1},
        {"aud": "other"},
        {"iss": "other"},
        {"sub": None},
        {"exp": None},
    ]:
        assert not await auth.verify_token(jwt.encode(claims | patch, private, algorithm="RS256"))
    with pytest.raises(ValueError):
        verifier(Settings())


async def test_verified_registration_and_scope_matrix():
    from suppliermcp.access import AccessDenied, require_scope
    from suppliermcp.mcp.auth import identity_from_token

    private, public = keys()
    both = "catalog:read documents:read"
    auth = verifier(
        Settings(
            auth_public_key=public,
            auth_clients={
                "ordinary": {},
                "codex": {"document_subjects": ["alice"]},
                "chatgpt": {"document_subjects": ["alice"]},
            },
            auth_legacy_subjects=["alice"],
        )
    )
    claims = {"sub": "alice", "iss": "suppliermcp", "aud": "suppliermcp", "exp": time.time() + 600}

    async def identity(patch, key=private):
        token = jwt.encode(claims | patch, key, algorithm="RS256")
        return identity_from_token(await auth.verify_token(token))

    for client in ["codex", "chatgpt"]:
        personal = await identity({"client_id": client, "scope": both})
        require_scope(personal, "catalog:read")
        require_scope(personal, "documents:read")
    assert personal.principal != (await identity({"client_id": "codex", "scope": both})).principal
    for patch in [
        {},
        {"client_id": "ordinary", "scope": both},
        {"client_id": "codex", "scope": both, "sub": "bob"},
        {"client_id": "codex", "scope": "catalog:read"},
    ]:
        catalog = await identity(patch)
        require_scope(catalog, "catalog:read")
        with pytest.raises(AccessDenied) as err:
            require_scope(catalog, "documents:read")
        assert err.value.status_code == 403
    empty = await identity({"client_id": "codex"})
    for scope in ["catalog:read", "documents:read"]:
        with pytest.raises(AccessDenied) as err:
            require_scope(empty, scope)
        assert err.value.status_code == 403
    forged_key, _ = keys()
    for patch, key in [
        ({"client_id": "codex", "scope": both}, forged_key),
        ({"client_id": "codex", "azp": "ordinary", "scope": both}, private),
        ({"client_id": "unregistered", "scope": both}, private),
        ({"scope": both}, private),
        ({"sub": "bob"}, private),
        ({"client_id": "codex", "scope": both, "aud": "other"}, private),
        ({"client_id": "codex", "scope": both, "exp": time.time() - 1}, private),
    ]:
        with pytest.raises(AccessDenied) as err:
            await identity(patch, key)
        assert (err.value.status_code, str(err.value)) == (401, "unauthorized")
