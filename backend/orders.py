from fastapi import APIRouter, HTTPException, Request

from .catalog import fetch_rows, session_client

router = APIRouter()


def format_orders(client, rows, mine):
    if not rows:
        return []

    order_ids = [row["id"] for row in rows]
    lines = fetch_rows(
        client.table("order_items")
        .select("order_id,menu_item_id,quantity")
        .in_("order_id", order_ids)
    )

    item_ids = list({line["menu_item_id"] for line in lines})
    menu = []
    if item_ids:
        menu = fetch_rows(
            client.table("menu_items")
            .select("id,name")
            .in_("id", item_ids)
        )

    names = {item["id"]: item["name"] for item in menu}
    descriptions = {order_id: [] for order_id in order_ids}

    for line in lines:
        name = names.get(
            line["menu_item_id"],
            "Unavailable menu item",
        )
        descriptions[line["order_id"]].append(
            f'{name} × {line["quantity"]}'
        )

    return [
        {
            "id": row["id"],
            "business_id": row["business_id"],
            "items": ", ".join(descriptions[row["id"]])
                     or "No item details available",
            "total": float(row["total"]),
            "date": row.get("pickup_date")
                    or row["created_at"],
            "status": row["status"],
            "mine": mine,
        }
        for row in rows
    ]


@router.get("/api/orders/mine")
def own_orders(request: Request):
    client = session_client(request)
    rows = fetch_rows(
        client.table("orders")
        .select(
            "id,customer_id,business_id,status,total,"
            "created_at,pickup_date"
        )
        .eq("customer_id", request.state.user["id"])
        .order("created_at", desc=True)
    )
    return format_orders(client, rows, mine=True)


@router.get("/api/owner/orders")
def business_orders(request: Request):
    business_id = request.state.user.get("business_id")
    if not business_id:
        raise HTTPException(403, "No business assigned.")

    client = session_client(request)
    rows = fetch_rows(
        client.table("orders")
        .select(
            "id,customer_id,business_id,status,total,"
            "created_at,pickup_date"
        )
        .eq("business_id", str(business_id))
        .order("created_at", desc=True)
    )
    return format_orders(client, rows, mine=False)
