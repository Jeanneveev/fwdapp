import pytest
import jwt as pyjwt
import os
# Use unconditional assignment so env vars are set before server.py is imported
# (server.py reads them at module level; setdefault would be unsafe if env was pre-set)
os.environ["APP_JWT_SECRET"]   = "test-secret"
os.environ["APP_JWT_ISSUER"]   = "my-thin-bridge"
os.environ["APP_JWT_AUDIENCE"] = "my-attached-app"

from server import _validate_jwt, Room, Member, Motion

SECRET = "test-secret"

def make_token(sub="user1", name="Alice", exp_offset=3600):
    import time
    return pyjwt.encode(
        {"sub": sub, "name": name, "iss": "my-thin-bridge",
         "aud": "my-attached-app", "exp": int(time.time()) + exp_offset},
        SECRET, algorithm="HS256"
    )

def test_validate_jwt_valid():
    token = make_token()
    claims = _validate_jwt(token)
    assert claims["sub"] == "user1"

def test_validate_jwt_expired():
    token = make_token(exp_offset=-10)
    with pytest.raises(Exception):
        _validate_jwt(token)

def test_validate_jwt_wrong_audience():
    import time
    bad = pyjwt.encode(
        {"sub": "x", "iss": "my-thin-bridge", "aud": "wrong", "exp": int(time.time()) + 3600},
        SECRET, algorithm="HS256"
    )
    with pytest.raises(Exception):
        _validate_jwt(bad)
