"""Session reader shared by every protected route.
Member 3 implements login/session creation using this documented table shape.
"""
import hashlib
import os
import sqlite3
import time
from pathlib import Path
from fastapi import HTTPException, Request


def current_user(request: Request) -> dict:
    token = request.cookies.get('simplecater_session')
    path = Path(os.environ.get('SIMPLECATER_DB', '/data/simplecater.db'))
    if not token or not path.is_file():
        raise HTTPException(401, 'Sign in first.')
    try:
        with sqlite3.connect(path) as db:
            db.row_factory = sqlite3.Row
            row = db.execute(
                'SELECT u.id, u.role, u.business_id FROM sessions s '
                'JOIN users u ON u.id=s.user_id '
                'WHERE s.token_hash=? AND s.expires_at>?',
                (hashlib.sha256(token.encode()).hexdigest(), time.time()),
            ).fetchone()
    except sqlite3.Error:
        raise HTTPException(401, 'Session unavailable. Sign in again.') from None
    if row is None or row['role'] not in ('customer', 'owner'):
        raise HTTPException(401, 'Session expired. Sign in again.')
    return dict(row)
