from binascii import Error as Base64Error

from cryptography.exceptions import InvalidTag
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from .catalog import fetch_rows, session_client
from .profile_crypto import encrypt_profile, decrypt_profile

router = APIRouter()


class ProfileInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(default="", max_length=120)
    phone: str = Field(default="", max_length=40)
    address: str = Field(default="", max_length=500)


def customer_id(request):
    user = request.state.user
    if user["role"] != "customer":
        raise HTTPException(403, "Customer access required.")
    return user["id"]


@router.get("/api/profile")
def read_profile(request: Request):
    user_id = customer_id(request)
    client = session_client(request)
    rows = fetch_rows(
        client.table("profiles")
        .select("encrypted_profile")
        .eq("id", user_id)
    )
    if len(rows) != 1:
        raise HTTPException(403, "Customer profile is not configured.")

    envelope = rows[0]["encrypted_profile"]
    if envelope is None:
        return ProfileInput().model_dump()

    try:
        plaintext = decrypt_profile(user_id, envelope)
        return ProfileInput.model_validate(plaintext).model_dump()
    except (
        InvalidTag, ValueError, KeyError, TypeError,
        OSError, RuntimeError, Base64Error,
    ):
        raise HTTPException(
            503, "Unable to read the encrypted profile."
        ) from None


@router.put("/api/profile")
def save_profile(body: ProfileInput, request: Request):
    user_id = customer_id(request)

    try:
        envelope = encrypt_profile(user_id, body.model_dump())
    except (OSError, RuntimeError, ValueError):
        raise HTTPException(
            503, "Profile encryption is unavailable."
        ) from None

    client = session_client(request)
    rows = fetch_rows(
        client.table("profiles")
        .update({"encrypted_profile": envelope})
        .eq("id", user_id)
    )
    if len(rows) != 1:
        raise HTTPException(403, "Profile could not be saved.")

    return {"saved": True}
