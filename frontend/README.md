# SimpleCater: separate customer and owner interfaces

Frontend-only preview: `python3 -m http.server 4319` from this folder. Open `/index.html`. Sample accounts: `customer` / `demo`, `owner` / `demo`. Browser demo session is simulated and editable; never use real credentials or profile data. No admin remains.

- index.html: sign-in; no workspace/role switch.
- customer.html: menu, recommendation with explanation, cart, own orders/profile.
- owner.html: business orders and sales assistant only.
- app.js / styles.css: UI behavior and approved design.
- services.js: explicit demo and real API adapters.
- config.js: static preview defaults to demo. FastAPI serves an API-mode config automatically.
- fixtures.js: synthetic customer/order/menu records, no admin data.

Signed-in account determines its workspace. Opening the other page shows access denied in the demo. Real security is enforced by backend/app.py with backend/auth.py: protected HTML and API routes require a valid session and correct role. Business/member ownership checks must be implemented in data queries as specified in ../docs/API_CONTRACT.md.

The server shell deliberately returns 501 for unfinished login/business/AI endpoints. No fake model or crypto runs in connected mode. Member assignments and resource credits live under ../docs/. Profile save is plain in-memory data in demo; planned backend encryption is explicitly separate.
