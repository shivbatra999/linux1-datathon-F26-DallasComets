from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from .catalog import fetch_rows, session_client
from .customer_recommendations import customer_picks
from .predictive import ModelUnavailable

router = APIRouter()


class RecommendationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    business_id: UUID
    selected_item_id: UUID
    cart_item_ids: list[UUID] = Field(default_factory=list, max_length=50)


@router.post("/api/ai/recommendations")
def recommendations(body: RecommendationInput, request: Request):
    user = request.state.user
    if user["role"] != "customer":
        raise HTTPException(403, "Customer access required.")

    client = session_client(request)
    business_id = str(body.business_id)

    businesses = fetch_rows(
        client.table("businesses")
        .select("id")
        .eq("id", business_id)
        .eq("is_active", True)
    )
    if not businesses:
        raise HTTPException(404, "Business is unavailable.")

    menu = fetch_rows(
        client.table("menu_items")
        .select("id,is_available,model_item_id")
        .eq("business_id", business_id)
        .eq("is_available", True)
    )

    selected_id = str(body.selected_item_id)
    cart_ids = [str(value) for value in body.cart_item_ids]
    available_ids = {row["id"] for row in menu}

    if selected_id not in available_ids or any(
        item_id not in available_ids for item_id in cart_ids
    ):
        raise HTTPException(
            400, "Items must be available from the selected business."
        )

    orders = fetch_rows(
        client.table("orders")
        .select("id")
        .eq("business_id", business_id)
        .eq("customer_id", user["id"])
        .ilike("status", "completed")
    )

    history = []
    if orders:
        order_ids = [row["id"] for row in orders]
        lines = []
        for offset in range(0, len(order_ids), 100):
            lines.extend(fetch_rows(
                client.table("order_items")
                .select("order_id,menu_item_id")
                .in_("order_id", order_ids[offset:offset + 100])
            ))

        grouped = {order_id: [] for order_id in order_ids}
        for line in lines:
            if line["order_id"] in grouped:
                grouped[line["order_id"]].append(line["menu_item_id"])
        history = list(grouped.values())

    try:
        return customer_picks(menu, history, selected_id, cart_ids)
    except ModelUnavailable:
        raise HTTPException(
            503, "Recommendation model is unavailable."
        ) from None
    except ValueError:
        raise HTTPException(
            503, "Recommendation configuration is unavailable."
        ) from None
