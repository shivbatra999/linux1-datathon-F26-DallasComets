# Current API contract

Base: `/api`. JSON responses are unwrapped. IDs are UUID strings unless explicitly described as internal model IDs. Errors use `{"detail": ...}`; validation errors may contain FastAPI's structured error list.

Protected routes validate the `simplecater_session` cookie through Supabase and read the user's own protected profile for role/business. Unsafe API requests, including login and logout, require an exact trusted `Origin`. API mode serves frontend configuration from `/config.js`.

## Identity

| Method/path | Input | Success |
|---|---|---|
| POST `/auth/login` | `{email,password}` | 200 `{id,role,business_id}` and HttpOnly cookie |
| GET `/auth/me` | Cookie | 200 same identity shape |
| POST `/auth/logout` | Optional cookie | 204 and cleared cookie; repeat logout supported |

The frontend form calls its field username but the service adapter sends `email`. Cookies are SameSite=Strict and Secure when configured for HTTPS. Loopback HTTP is supported for SSH-tunnel testing. No refresh-token flow or self-service registration UI is implemented. Logout calls Supabase with local scope; do not claim it immediately invalidates every copied access JWT. Authentication outage/error responses can be 503.

## Catalog and orders

| Method/path | Role/scope | Success |
|---|---|---|
| GET `/businesses` | Authenticated | Active `{id,name,is_active}` rows |
| GET `/businesses/{business_id}/menu` | Customer | Menu array |
| GET `/owner/menu` | Owner's session business | Menu array |
| GET `/orders/mine` | Customer's session identity | Own order display array |
| GET `/owner/orders` | Owner's session business | Business order display array |
| POST `/orders` | Customer | 201 `{id,status:"pending"}` |

Menu shape: `{id,business_id,name,desc,price,category,tag,img,is_available}`. Current catalog presentation uses a generic Lunch category and photo; it does not yet reflect the predictor's separate category mapping.

Order display shape: `{id,business_id,items,total,date,status,mine}`. `items` is a formatted description; `date` is pickup date, falling back to creation timestamp for older records. Totals are numeric USD. Missing/inaccessible historical menu names may display as unavailable.

Checkout input:

```json
{
  "business_id": "<business UUID>",
  "pickup_date": "<YYYY-MM-DD, today or later in America/Chicago>",
  "items": [{"menu_item_id": "<menu UUID>", "quantity": 2}]
}
```

The cart has 1–50 distinct items; quantities are strict integers from 1–1000. Extra fields, including client prices/totals, are rejected. The Supabase function validates business/item availability, captures database prices, computes totals, and saves order plus lines atomically. There is no idempotency key: after an ambiguous timeout check history before retrying. No payment is collected and no order-status editing API is implemented.

## Customer profile

- GET `/profile` → `{name,phone,address}`. Blank fields if no encrypted profile exists.
- PUT `/profile` with the same fields → `{"saved":true}`.
- Limits: name 120, phone 40, address 500 characters; whitespace stripped, extra fields rejected.
- Session identity controls the row. The backend encrypts before storage and decrypts on an authorized read. Email remains managed by Supabase Auth, not this form.

## Customer AI

POST `/ai/recommendations`:

```json
{
  "business_id": "<business UUID>",
  "selected_item_id": "<menu UUID>",
  "cart_item_ids": ["<menu UUID>"]
}
```

Returns at most two `{item_id,reason,source}` objects. Output IDs are database UUIDs. Inputs must reference available items in the active requested business; invalid selection/cart items return 400. Cart IDs are limited to 50; extra identity fields are rejected with 422. Only the session customer's completed orders at that business are queried. Customer access does not imply access to other customers' history.

Sources:
- `model`: trained ranking with a minimum of three qualifying co-occurrences for a pairing explanation.
- `fallback`: measured order popularity, not a model pairing claim.
- `random`: exploratory item with no supporting history; never describe as measured confidence.

An unmapped selected item uses personal-history popularity only and may return an empty array. Mapped-history denominators can be smaller than all completed orders. Selected/cart/unavailable items are excluded by the adapter. Model/configuration outages return 503.

## Owner AI

POST `/ai/summary` → `{text,prediction_reason,source:"model"}`. `prediction_reason` is an array of `{item_id,reason,source}`; the outer source describes the generated summary, not proof that each recommendation was model-ranked.

The backend reads only its owner's business: completed order IDs/totals, available menu IDs/names/mappings, and order/menu IDs for those lines. It sums completed-order value, computes prediction evidence, and sends Granite the count, total, reasons and sources. Prediction IDs are removed from the prompt. Browser display can still include explanation strings derived from these results.

Granite has no application tools. Output is text; generation is capped at 48 tokens and the backend timeout is capped at 180 seconds. Output cleanup is heuristic, not a formal factuality or prompt-injection guarantee. Unavailable/invalid inference returns 503, not a demo answer. Frontend timeout is currently 120 seconds and can expire sooner than the backend.

## Pages and errors

`/customer.html` and `/owner.html` are guarded server-side. Anonymous access is 401; wrong role is 403. `/health` is a process health response only and does not prove Supabase/model readiness or identify the deployed commit. Unknown/unimplemented `/api/*` routes return 501.
