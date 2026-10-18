# Remaining work and deliberate limits

## Before the final demonstration

1. Reconcile the LinuxONE deployment checkout's divergent local main with origin/main while preserving local commits. The Actions workflow requires a clean fast-forwardable main; confirm the latest run actually succeeded.
2. Replace obsolete SQLite session tests with current Supabase/mocked-auth regression tests. Preserve the manual security evidence and add regression coverage for the stripped Granite prompt IDs.
3. Export the complete existing Supabase schema, profile provisioning trigger, grants, and RLS policies. Current migrations 001–003 assume that setup already exists.
4. Record final container/package/model/llama.cpp revisions. Pin remaining dependencies after validation; the generator currently clones llama.cpp's moving default branch.
5. Complete resource/license notices and team contribution credits; record both AI runtimes on LinuxONE and use the organizers' current submission requirements.

## Known application behavior

- Two roles only; no admin, registration UI, widget marketplace, payment processing, menu editor, or order-status editor.
- Checkout creates pending orders; AI uses completed orders. New orders do not automatically affect AI history. Any synthetic completed demonstration data must be clearly identified.
- Customer bootstrap selects the first active business, not a business picker. Display branding and some counts/categories/photos remain hard-coded or generic.
- Pickup defaults/minimum date in frontend code are fixed to October 2026; the database enforces today's America/Chicago date. Update UI dates before later demos.
- Six matching Store 1 menu items have explicit training IDs. Other items remain orderable. An unmapped selection uses measured personal-history popularity and may have no suggestions. No model semantics should be guessed for unrelated foods.
- Mapped predictions currently use mapped, available items and qualifying completed-history baskets. Their denominator can differ from all completed orders.
- Random exploratory suggestions are not learned recommendations. Popularity fallback is not a model pairing claim. Recommendation evidence counts baskets, not quantities sold.
- Cold-start/empty suggestion wording may imply items are already in the cart even when no mapped evidence exists. Frontend source presentation can be improved.
- Owner summaries are generated text. Constraints and cleanup are heuristic; there is no systematic output-number verifier or full prompt-injection evaluation.
- Browser timeout is 120 seconds; backend generation can wait 180 seconds. Long inference may succeed on the server after the browser times out.
- Owner summary queries do not implement full pagination; large histories may be limited by PostgREST defaults/URL size. This prototype uses small demonstration data.

## Security/deployment boundaries

- Supabase Auth/PostgreSQL are external hosted services. Encryption/inference run on LinuxONE; this is not an entirely on-premises data system.
- PQC-assisted encryption covers contact profile JSON, not orders/identifiers/email or HTTPS.
- Keys have a version field but no rotation workflow. Back up the existing key safely. A read-only mount does not prevent a compromised backend from reading it.
- No login rate-limiting code or refresh-token workflow is implemented. Re-login is required at token expiry. Do not claim universal immediate access-JWT revocation on logout.
- Only SSH-tunnel/loopback access was demonstrated; public deployment requires HTTPS and trusted origin/ingress configuration.
- Duplicate checkout after ambiguous retries is possible; no idempotency key exists.
- Remaining column grants and policy combinations require full review; passed isolation checks do not constitute a full audit.

## Out of scope until core acceptance is complete

Payment processing, financial-data storage, autonomous AI actions, drag-and-drop site builders, elaborate fulfillment workflows, and additional AI frameworks solely for scoring.
