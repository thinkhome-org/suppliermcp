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
    auth = verifier(Settings(auth_public_key=public))
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
