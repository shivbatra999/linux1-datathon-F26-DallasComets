from datetime import date
from uuid import UUID

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from postgrest.exceptions import APIError

from .catalog import session_client

router = APIRouter()


class OrderItem(BaseModel):
    model_config = {"extra": "forbid"}

    menu_item_id: UUID
    quantity: int = Field(strict=True, ge=1, le=1000)


class OrderInput(BaseModel):
    model_config = {"extra": "forbid"}

    business_id: UUID
    pickup_date: date
    items: list[OrderItem] = Field(min_length=1, max_length=50)


@router.post("/api/orders", status_code=201)
def create_order(body: OrderInput, request: Request):
    if request.state.user["role"] != "customer":
        raise HTTPException(403, "Customer account required.")

    ids = [item.menu_item_id for item in body.items]
    if len(ids) != len(set(ids)):
        raise HTTPException(400, "Duplicate cart item.")

    client = session_client(request)
    data = body.model_dump(mode="json")

    try:
        result = client.rpc(
            "simplecater_place_order",
            {
                "p_business_id": data["business_id"],
                "p_pickup_date": data["pickup_date"],
                "p_items": data["items"],
            },
        ).execute()
    except APIError as error:
        if error.code in (
            "P0001", "22023", "22P02", "22003", "23514",
        ):
            raise HTTPException(
                400,
                "Order rejected. Check the business, items, "
                "quantities, and pickup date.",
            ) from None
        if error.code == "42501":
            raise HTTPException(
                403, "Order access denied."
            ) from None
        raise HTTPException(
            503, "Order service is unavailable."
        ) from None
    except httpx.RequestError:
        raise HTTPException(
            503,
            "Order outcome could not be confirmed. "
            "Check your order history before retrying.",
        ) from None

    return {
        "id": result.data,
        "status": "pending",
    }
