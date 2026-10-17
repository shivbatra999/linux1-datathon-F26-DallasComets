# Five-person implementation plan

Frontend design/integration points already exist. Each member owns a small module set; API_CONTRACT.md freezes handoff shapes.

| Member | Own files/work | Handoff and acceptance |
|---|---|---|
| 1: frontend and final integration | frontend/* | Existing split pages, sign-in/profile, cart, suggestions, summary. Connect completed endpoints, handle failures, record flow. Check both roles cannot navigate into the other workspace in API mode. |
| 2: backend and database | backend/app.py, db.py, orders.py, catalog.py | Implement scoped menu/orders/profile routes, six SQLite tables, synthetic seeds, server totals. Use member 3 session dependency. Provide scoped model inputs to members 4/5. |
| 3: identity and PQC | backend/auth.py, profiles.py, profile_crypto.py | Finish login/logout/session creation, Argon2id, expiration and rate limits; customer-only encrypted profile save/read. Verify tamper rejection, key persistence and cross-role/customer isolation. |
| 4: predictive AI and evidence | backend/predictive.py, evaluation/, model artifact | Train catering item recommender, split by whole order, compare with popularity. Return 2 IDs and verified evidence explanations. Same predictive function feeds customer suggestions and owner summary. |
| 5: generative AI and LinuxONE | backend/generative.py, Dockerfile, requirements-ai.txt | Run local small GGUF model, explain actual predictions and verified totals. Verify native libraries on LinuxONE, finish container/HTTPS deployment, capture runtime evidence and exact dependency/model versions. |

## Integration sequence

1. Members 2/3 agree on schema/session helper; all agree on API contract. Complete required event labs.
2. Member 1 uses isolated browser demo. Member 2 builds routes. Member 3 builds auth/crypto. Members 4/5 run on fixed synthetic inputs independently.
3. Members 2/4 connect predictor; members 2/5 connect grounded summary using the same prediction. Member 3 connects encrypted profiles. No models get unrestricted DB access.
4. Member 1 uses API mode. Test both roles and actual ownership filters, not just hidden buttons. Record failures; no demo fallback.
5. Member 5 runs assembled container on LinuxONE. Each member demonstrates their contribution. Member 1 assembles <=3-minute video; all supply measured evidence and beneficiary research.

## Done means

Customer signs in, selects food, sees a justified prediction, places order, and reads only their orders/profile. Owner signs in separately, sees only their business orders and grounded AI summary. Customer owner-page/API attempts are denied server-side. Stored profile encrypted; identifiers absent from model inputs. Both AI runtimes execute on LinuxONE. Resources credited, synthetic data disclosed, no unimplemented feature claimed.

No new Git push or Sites publication is included in this local revision.
