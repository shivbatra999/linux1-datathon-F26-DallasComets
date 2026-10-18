# Five workstreams and final handoffs

This is a responsibility split. Assign actual names based on the team's real contributions; it does not certify five registered members.

| Workstream | Implemented area | Final handoff |
|---|---|---|
| 1: frontend and integration | Customer/owner pages, cart, profile form, suggestions, summary | Fix generic/empty labels and date defaults; capture both browser flows |
| 2: database and orders | Supabase catalog, scoped reads, atomic server-priced checkout, migrations | Export full schema/RLS/provisioning; document synthetic records and completed status |
| 3: identity and PQC | Supabase sessions/role checks, encrypted profile API, persistent keys, container key mount | Preserve keys and backup procedure; save repeatable auth/crypto/isolation tests |
| 4: predictive AI | BernoulliNB artifact, synthetic training/evaluation, explicit mappings, customer and owner evidence | Verify model/fallback/random labels, unmapped cases, held-out metrics, source/version records |
| 5: generative AI and LinuxONE | Granite/llama.cpp, minimal prompt, container builds/private network | Verify real inference, factual summaries and timeout behavior; record final runtime and deployment evidence |

## Current integration status

Both browser flows were reported working on LinuxONE. Customer and owner AI use explicit menu model IDs. The live examples used measured popularity fallbacks; a controlled test exercised model pairing evidence. The owner prompt strips prediction IDs and sends verified totals plus reasons/sources only. Payments remain deferred.

## Final acceptance sequence

1. Confirm source/image deployment and GitHub Actions status; do not infer running code from host branch alone.
2. Sign in as customer, select food, inspect source/evidence, add suggested item and confirm exclusion, place a pickup order, verify own history, save/read encrypted profile.
3. Sign in as owner, verify business scope, generate real Granite insights, compare completed-order count/value with database results.
4. Save tests/evidence for cross-role, cross-customer, cross-business, tamper/AAD, key persistence, and minimal Granite request data.
5. Refresh package/model/resource credits and record a concise LinuxONE demonstration within the published event limit.

No claim of community impact, real demand forecasting, hardware acceleration, or model accuracy should exceed measured evidence. Verify organizer requirements for accepted AI frameworks, originality, permitted resources, and final submission format rather than relying on this plan as official rules.
