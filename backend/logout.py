import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from .config import (
    SIMPLECATER_ORIGIN,
    SUPABASE_URL,
    SUPABASE_PUBLISHABLE_KEY,
)

router = APIRouter()


@router.post("/api/auth/logout")
def logout(request: Request):
    token = request.cookies.get("simplecater_session")
    remote_failed = False

    if token:
        if not SUPABASE_URL or not SUPABASE_PUBLISHABLE_KEY:
            remote_failed = True
        else:
            try:
                result = httpx.post(
                    SUPABASE_URL.rstrip("/") + "/auth/v1/logout",
                    params={"scope": "local"},
                    headers={
                        "apikey": SUPABASE_PUBLISHABLE_KEY,
                        "Authorization": "Bearer " + token,
                    },
                    timeout=15,
                )
                remote_failed = result.status_code not in (
                    200, 204, 401, 403,
                )
            except httpx.RequestError:
                remote_failed = True

    if remote_failed:
        response = JSONResponse(
            status_code=503,
            content={
                "detail": (
                    "Local cookie cleared, but Supabase logout "
                    "could not be confirmed."
                )
            },
        )
    else:
        response = Response(status_code=204)

    response.delete_cookie(
        key="simplecater_session",
        path="/",
        httponly=True,
        secure=SIMPLECATER_ORIGIN.startswith("https:"),
        samesite="strict",
    )
    response.headers["Cache-Control"] = "no-store"
    return response
