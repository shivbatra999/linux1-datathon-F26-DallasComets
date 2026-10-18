# SimpleCater frontend

Plain HTML/CSS/JavaScript modules. Customer and owner pages are separate; there is no admin page. No frontend build step is required.

## Real application

Run the backend using [deployment instructions](../docs/DEPLOYMENT.md). Open `/index.html` through the configured same-origin address. Backend `/config.js` selects API mode. Supabase account email is entered in the form labeled Username; the adapter sends `{email,password}`.

Customers browse the first active business, view suggestions, use the separate cart/floating cart button, place pickup orders, view own history, and edit name/phone/address through the encrypted profile API. Owners see their business orders and request a Granite summary. APIs enforce access in addition to page guards; hiding links is not the security mechanism.

## Static visual preview only

```bash
cd frontend
python3 -m http.server 4319
```

Open `http://127.0.0.1:4319/index.html`. The committed static config selects demo mode. Sample usernames are customer or owner; password demo. Sessions use editable sessionStorage; profiles/orders are in-memory samples. No real Supabase authentication, encrypted storage, or model inference occurs. Never enter real credentials/personal data into this preview.

## Integration details

`services.js` switches API/demo adapters. The API sends UUIDs for business/menu identifiers and includes same-origin cookies. `app.js` renders reasons and owner output as escaped text. Customer source labels are returned by the API; do not present random/fallback suggestions as model confidence. Owner outer source=model describes text generation, not necessarily its recommendation source.

Some branding, catalog categories/photos, counts, and date defaults are still fixed; see [limits](../docs/KNOWN_LIMITATIONS.md). Browser API timeout is 120 seconds while generation may take 180 seconds on the backend. No frontend payment or fulfillment editing flow is connected.
