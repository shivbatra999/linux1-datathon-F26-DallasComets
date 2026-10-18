"""Role-guarded server shell. Business/model routes deliberately remain unimplemented."""
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from .auth import current_user

ROOT = Path(__file__).resolve().parent.parent / 'frontend'
app = FastAPI(title='SimpleCater', docs_url=None, redoc_url=None)
CUSTOMER = {'/api/orders/mine', '/api/orders', '/api/profile', '/api/ai/recommendations'}
OWNER = {'/api/owner/menu', '/api/owner/orders', '/api/ai/summary'}


@app.middleware('http')
async def protect(request: Request, call_next):
    path = request.url.path
    required = 'owner' if path in OWNER or path == '/owner.html' else (
        'customer' if path in CUSTOMER or path == '/customer.html' or path.startswith('/api/businesses/') else None)
    try:
        # All API routes except login require a real session. No demo account backdoor.
        if required or (path.startswith('/api/') and path != '/api/auth/login'):
            request.state.user = current_user(request)
            if required and request.state.user['role'] != required:
                raise HTTPException(403, 'This workspace is restricted.')
        if path.startswith('/api/') and request.method not in ('GET', 'HEAD', 'OPTIONS'):
            expected = os.environ.get('SIMPLECATER_ORIGIN', str(request.base_url).rstrip('/'))
            if request.headers.get('origin') != expected:
                raise HTTPException(403, 'Untrusted request origin.')
    except HTTPException as e:
        return JSONResponse({'detail': e.detail}, status_code=e.status_code)
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@app.get('/api/auth/me')
def me(request: Request):
    return request.state.user


@app.get('/config.js')
def config():
    return Response("export const config={mode:'api',apiBase:'/api',timeoutMs:120000};", media_type='text/javascript')


@app.get('/health')
def health():
    return {'status': 'ok', 'stage': 'integration-scaffold'}


@app.api_route('/api/{path:path}', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def integration_placeholder(path: str):
    raise HTTPException(501, 'This backend integration is not implemented yet.')


@app.get('/')
@app.get('/index.html')
def login_page():
    return FileResponse(ROOT / 'index.html')


@app.get('/customer.html')
def customer_page():
    return FileResponse(ROOT / 'customer.html')


@app.get('/owner.html')
def owner_page():
    return FileResponse(ROOT / 'owner.html')


@app.get('/{asset}')
def asset(asset: str):
    if asset not in {'app.js', 'services.js', 'fixtures.js', 'styles.css'}:
        raise HTTPException(404, 'Not-found.')
    return FileResponse(ROOT / asset)
