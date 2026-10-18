from uuid import UUID

import httpx
from fastapi import APIRouter, HTTPException, Request
from postgrest.exceptions import APIError

from .supabase_client import new_supabase_client

router = APIRouter()


def session_client(request):
    client = new_supabase_client()
    client.postgrest.auth(
        request.cookies["simplecater_session"]
    )
    return client


def fetch_rows(query):
    try:
        return query.execute().data or []
    except (APIError, httpx.RequestError):
        raise HTTPException(
            503, "Unable to load database records."
        ) from None


def menu_for_business(request, business_id):
    client = session_client(request)
    rows = fetch_rows(
        client.table("menu_items")
        .select("id,business_id,name,description,price,is_available")
        .eq("business_id", str(business_id))
        .order("name")
    )
    return [
        {
            "id": row["id"],
            "business_id": row["business_id"],
            "name": row["name"],
            "desc": row.get("description") or "",
            "price": float(row["price"]),
            "category": "Lunch",
            "tag": (
                "Available" if row["is_available"]
                else "Unavailable"
            ),
            "img": "photo-1512621776951-a57141f2eefd",
            "is_available": row["is_available"],
        }
        for row in rows
    ]


@router.get("/api/businesses")
def businesses(request: Request):
    client = session_client(request)
    return fetch_rows(
        client.table("businesses")
        .select("id,name,is_active")
        .eq("is_active", True)
        .order("name")
    )


@router.get("/api/businesses/{business_id}/menu")
def customer_menu(business_id: UUID, request: Request):
    return menu_for_business(request, business_id)


@router.get("/api/owner/menu")
def owner_menu(request: Request):
    business_id = request.state.user.get("business_id")
    if not business_id:
        raise HTTPException(403, "No business assigned.")
    return menu_for_business(request, business_id)
