from fastapi import APIRouter, HTTPException, Request
import httpx
from postgrest.exceptions import APIError

from .catalog import session_client
from .generative import GenerationUnavailable, owner_summary

router = APIRouter()


@router.post("/api/ai/summary")
def ai_summary(request: Request):
    business_id = request.state.user.get("business_id")
    if request.state.user.get("role") != "owner" or not business_id:
        raise HTTPException(403, "Owner business access is required.")
    try:
        return owner_summary(session_client(request), business_id)
    except GenerationUnavailable as error:
        raise HTTPException(503, str(error)) from None
    except (APIError, httpx.RequestError, KeyError, ValueError):
        raise HTTPException(503, "Unable to load verified business totals.") from None
