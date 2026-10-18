from urllib.parse import urlsplit

import httpx
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
from supabase_auth.errors import AuthApiError

from .config import SIMPLECATER_ORIGIN
from .identity import identity_from_user
from .supabase_client import new_supabase_client

router = APIRouter()


class LoginInput(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=1024)


@router.post("/api/auth/login")
def login(body: LoginInput, response: Response):
    origin = urlsplit(SIMPLECATER_ORIGIN)
    secure = origin.scheme == "https"

    if not secure and not (
        origin.scheme == "http"
        and origin.hostname in ("localhost", "127.0.0.1")
    ):
        raise HTTPException(503, "HTTPS is required for login.")

    client = new_supabase_client()

    try:
        result = client.auth.sign_in_with_password({
            "email": body.email.strip(),
            "password": body.password,
        })
    except AuthApiError as error:
        if error.status in (400, 401, 403, 422):
            raise HTTPException(
                401, "Unable to sign in with these credentials."
            ) from None
        raise HTTPException(
            503, "Authentication is temporarily unavailable."
        ) from None
    except httpx.RequestError:
        raise HTTPException(
            503, "Authentication is temporarily unavailable."
        ) from None

    identity = identity_from_user(result.user, client)
    session = result.session

    if not session or not session.access_token:
        raise HTTPException(401, "No valid session was returned.")

    lifetime = int(session.expires_in or 0)
    if lifetime <= 0:
        raise HTTPException(401, "Session has expired.")

    response.set_cookie(
        key="simplecater_session",
        value=session.access_token,
        max_age=lifetime,
        httponly=True,
        secure=secure,
        samesite="strict",
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    return identity
