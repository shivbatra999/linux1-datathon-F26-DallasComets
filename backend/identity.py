import httpx
from fastapi import HTTPException
from postgrest.exceptions import APIError


def identity_from_user(user, client):
    if not user or not user.id:
        raise HTTPException(401, "Invalid user.")

    try:
        result = (
            client.table("profiles")
            .select("id,role,business_id")
            .eq("id", str(user.id))
            .execute()
        )
    except (APIError, httpx.RequestError):
        raise HTTPException(
            503, "Unable to read account permissions."
        ) from None

    rows = result.data or []
    if len(rows) != 1:
        raise HTTPException(403, "Account profile is missing.")

    profile = rows[0]
    role = profile.get("role")
    business_id = profile.get("business_id")

    if role not in ("customer", "owner"):
        raise HTTPException(403, "Account role is not configured.")

    if role == "owner" and not business_id:
        raise HTTPException(403, "Business access is not configured.")

    return {
        "id": str(user.id),
        "role": role,
        "business_id": business_id if role == "owner" else None,
    }
