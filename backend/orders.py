from fastapi import APIRouter, Request

from .catalog import fetch_rows, session_client

router = APIRouter()


@router.get("/api/orders/mine")
def own_orders(request: Request):
    client = session_client(request)
    rows = fetch_rows(
        client.table("orders")
        .select("id,customer_id,business_id,status,total,created_at")
        .eq("customer_id", request.state.user["id"])
        .order("created_at", desc=True)
    )

    return [
        {
            "id": row["id"],
            "business_id": row["business_id"],
            "items": "Order details pending integration",
            "total": float(row["total"]),
            "date": row["created_at"],
            "status": row["status"],
            "mine": True,
        }
        for row in rows
    ]
