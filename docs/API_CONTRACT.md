# API contract: customer and owner only

Base `/api`. JSON responses, unwrapped. Errors `{"detail":"Safe message"}`. Cookie sessions; same-origin frontend and Origin/CSRF checks on writes. FastAPI shell denies cross-role page/API access; individual data queries still require ownership filters. Model/data endpoints currently return 501 until their owners implement them.

## Sessions

- POST `/auth/login` `{username,password}` -> `{id,role}` plus HttpOnly session cookie. Backend derives role; client cannot choose it.
- GET `/auth/me` -> `{id,role,business_id}`. Unauthenticated 401.
- POST `/auth/logout` -> 204; revoke session, clear cookie.

Two assigned accounts for demo event deployment; no registration/admin needed. Passwords set outside source. All initial records synthetic. SQLite sessions shape is specified in TECH_STACK.md.

## Customer only

- GET `/businesses/1/menu` -> array of `{id,name,desc,price,category,tag,img}`. `img` is validated Unsplash photo ID. USD numeric price; backend uses integer cents. MVP storefront fixed to business 1.
- GET `/orders/mine` -> array of `{id,items,total,date,status,mine:true}`. `items` is server-formatted display string, e.g. `Sandwich box × 2`; `date` pickup YYYY-MM-DD. Server filters by session customer ID.
- POST `/orders` `{business_id:1,pickup_date:"2026-10-18",items:[{menu_item_id:1,quantity:2}]}` -> created order with display shape above, 201. Recalculate price, validate positive integer quantities, item/business match and future pickup date; save atomically. Status can stay `Confirmed`. No payment collection.
- GET `/profile` -> `{name,email,phone}` for session customer; decrypt after authorization.
- PUT `/profile` `{name,email,phone}` -> same shape; validate/encrypt before storage. No profile data in AI inputs or logs.
- POST `/ai/recommendations` `{business_id:1,selected_item_id:1,cart_item_ids:[1]}` -> at most two `{item_id,reason,source:"model"}` objects. Exclude cart/unavailable items and enforce catalog scope. `reason` is verified aggregate evidence, e.g. `Appeared together in 24 of 80 qualifying orders.` ONLY use measured counts. If sparse, return empty array or explicitly labeled fallback; do not invent confidence. No customer IDs in model features.

## Owner only

- GET `/owner/menu` -> same menu shape; derive business from session.
- GET `/owner/orders` -> same order display shape, `mine:false`; scope by session business ID.
- POST `/ai/summary` -> `{text,prediction_reason,source:"model"}`. Backend builds allowed statistics, calls shared predictive function, then passes verified stats/prediction to local LLM. Text explains totals and the actual prediction. No HTML, unrestricted chat, customer details or database tools. Return 503 if model unavailable; no silent demo fallback.

## Functions shared between contributors

- Member 4: `recommend(menu_features, scoped_order_history, selected_item_id, cart_item_ids) -> list[{item_id, reason, source}]`. Receive prepared scoped data from member 2; no DB credentials.
- Member 5: `summarize(approved_stats, predictions) -> {text,prediction_reason,source}`. Load local model once, bound input/output size, serialize inference for the small VM.
- Member 3: `encrypt_profile(user_id, profile) -> encrypted_package`; `decrypt_profile(user_id, encrypted_package) -> profile`; role/session helpers shared with member 2.

No admin endpoints, business toggles, status workflow or publishing tools remain.
