# SimpleCater frontend

Approved interactive frontend prototype for the IBM Z Datathon.

## Run locally

From this directory:

```sh
python3 -m http.server 8000
```

Open http://localhost:8000. There is no dependency installation or build step.

## Included views

- **Customer:** menu filters, contextual pairing previews, a separate cart tab, a floating cart button, pickup ordering, and order history.
- **Business owner:** sample orders, order totals, menu-item count, and an AI sales-summary preview.
- **Admin:** business accounts with confirmation before enabling or pausing them.

The role switch is a design-preview control, not authentication. Orders and account changes exist only in page memory and reset on reload. Pairings and generated summaries are illustrative; no AI model is called.

## Backend integration

Replace the sample arrays and interaction handlers in `index.html` with calls to the team's backend for authentication, authorized menu/order access, and predictive/generative AI. Enforce authorization on the server. Customer profile encryption and password hashing belong in the backend and are not implemented in this frontend.

The page loads fonts from Google Fonts and photographs from Unsplash, so those assets require internet access. No payments, database, credentials, or LinuxONE deployment configuration are included.
