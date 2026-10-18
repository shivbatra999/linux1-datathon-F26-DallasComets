"""Validate Supabase access tokens and return authorized identity."""
import httpx
from fastapi import HTTPException, Request
from supabase_auth.errors import AuthApiError

from .identity import identity_from_user
from .supabase_client import new_supabase_client


def current_user(request: Request) -> dict:
    token = request.cookies.get("simplecater_session")

    if not token:
        raise HTTPException(401, "Sign in first.")

    client = new_supabase_client()

    try:
        result = client.auth.get_user(token)
    except AuthApiError as error:
        if error.status in (400, 401, 403, 404, 422):
            raise HTTPException(
                401, "Session invalid or expired. Sign in again."
            ) from None
        raise HTTPException(
            503, "Authentication is temporarily unavailable."
        ) from None
    except httpx.RequestError:
        raise HTTPException(
            503, "Authentication is temporarily unavailable."
        ) from None

    client.postgrest.auth(token)
    return identity_from_user(result.user, client)
