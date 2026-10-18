from fastapi import HTTPException
from supabase import create_client
from supabase.lib.client_options import SyncClientOptions as ClientOptions

from .config import (
    SUPABASE_URL,
    SUPABASE_PUBLISHABLE_KEY,
    supabase_configured,
)


def new_supabase_client():
    if not supabase_configured():
        raise HTTPException(
            status_code=503,
            detail="Authentication is not configured yet.",
        )

    return create_client(
        SUPABASE_URL,
        SUPABASE_PUBLISHABLE_KEY,
        options=ClientOptions(
            auto_refresh_token=False,
            persist_session=False,
        ),
    )
