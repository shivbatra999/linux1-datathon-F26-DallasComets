# SimpleCater: minimum stack, two roles

One LinuxONE VM, one backend process, one SQLite database, and local predictive/generative inference. Customer and business owner only. No admin, widget marketplace, payment system, vector database, or external model API.

| Feature | Tool | State |
|---|---|---|
| Sign-in/customer/owner pages | HTML, CSS, JavaScript modules + fetch | Implemented; demo and API adapters |
| API, role boundaries, static assets | FastAPI + Uvicorn | Role-guarded shell implemented; business routes remain 501 |
| Single database | Python sqlite3 | Session reader implemented; full schema/seeding assigned to member 2 |
| Passwords and sessions | argon2-cffi + Python secrets/hashlib | Session verification implemented; login/session issuance assigned to member 3 |
| Customer profiles | cryptography + liboqs-python/native liboqs | Planned ML-KEM-768 -> HKDF-SHA-256 -> AES-256-GCM helper |
| Pairing predictions | scikit-learn | Planned trained classifier; frontend accepts item ID + evidence explanation |
| Grounded sales summaries | llama-cpp-python + one small GGUF model | Planned local model; explanation includes actual predictive result |
| Container deployment | Dockerfile usable with Docker/Podman | Core-server image definition added; not built/verified on LinuxONE |
| HTTPS | Existing VM ingress, otherwise supported HTTPS proxy | Configure on actual LinuxONE host |

Model candidate: IBM Granite 3.3 2B Instruct, using a compatible GGUF conversion with exact source/license documented once selected. Do not claim downloaded weights or working inference yet. Validate model memory and both AI runtimes on s390x before final package pinning. No second AI framework added solely for scoring: confirm event acceptance of scikit-learn and llama.cpp as the requested pair.

## Deployment

Frontend-only preview: `cd frontend && python3 -m http.server 4319`. Sign in with sample `customer` or `owner`, password `demo`. Demo sessions are editable browser state and NOT a security boundary. All demo profiles/orders are synthetic and reset on page reload.

Core server: create a virtual environment, `pip install -r requirements.txt`, then `uvicorn backend.app:app --host 127.0.0.1 --port 8000`. It serves API mode automatically through `/config.js`; `/owner.html` and `/customer.html` are checked server-side. Until login and data routes are implemented, sign-in returns 501. Never bypass this to expose owner data.

Container shell: `docker build -t simplecater .` (or Podman). Mount persistent `/data` and a separate read-only secrets directory. Install tested native AI/PQC dependencies and add their files before recording actual inference. The supplied Dockerfile intentionally builds only the guarded integration shell. It is not a complete AI deployment. `requirements-ai.txt` lists the remaining runtime packages. Pin versions after successful LinuxONE installation; do not claim untested compatibility.

## Security contract

- Session cookie: `simplecater_session`; HttpOnly, Secure in HTTPS, SameSite=Strict. Store SHA-256 of random opaque session token; expire/revoke sessions. Login must rate-limit attempts.
- users requires `id`, `role` (`customer`/`owner`), `business_id`; sessions requires `token_hash`, `user_id`, `expires_at` (Unix seconds). Backend reader checks these tables. Finish remaining fields per API contract.
- Set SIMPLECATER_DB to persistent SQLite path and SIMPLECATER_ORIGIN to trusted HTTPS origin. Unsafe API calls require matching Origin. Keep backend behind trusted ingress; do not accept arbitrary forwarded host headers.
- Passwords are Argon2id hashes. Customer profile JSON contains name/email/phone; encrypt using per-save encapsulation and fresh AES-GCM nonce, user ID as AAD. Save ciphertext/tag, KEM ciphertext, nonce, key version in users. Private key stays outside SQLite/Git and survives restart.
- Role guard is only the first check: data queries MUST scope orders to customer ID or owner business ID. Owner requests do not accept a client-selected business.
- AI receives item IDs/counts/totals only, never profiles or credentials. Models do not open SQLite, execute commands, or publish changes. Backend computes supporting counts; LLM explains supplied facts.
- PQC protects stored profiles only, not HTTPS or a compromised backend. OQS use is a prototype.

## Evidence for submission

Record real LinuxONE instance/container plus both model executions, held-out prediction vs popularity baseline, factual-summary checks, profile encryption round trip, tamper rejection, and denied cross-role/business/customer requests. Report measured values only. Research the small-caterer beneficiary population; no invented impact or Telum claims.
