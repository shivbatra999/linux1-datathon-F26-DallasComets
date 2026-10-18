# Implemented tech stack

| Responsibility | Tool | Actual use |
|---|---|---|
| Browser | HTML, CSS, JavaScript modules, Fetch | Separate customer and owner pages; no frontend build framework |
| Backend | Python, FastAPI, Uvicorn | Static pages, authentication, authorization, application and AI endpoints |
| Identity | Supabase Auth / Python SDK | Email/password login and access-token validation; passwords are not managed by custom Argon2 code |
| Database | Supabase PostgreSQL / PostgREST | Five public tables, RLS, and an atomic checkout function |
| Prediction | scikit-learn BernoulliNB, NumPy, joblib | Saved model ranking plus measured evidence/fallback logic |
| Generation | IBM Granite 4.2 3B GGUF, llama.cpp | Owner summaries over verified business facts |
| Profile encryption | Native liboqs + liboqs-python, cryptography | ML-KEM-768, HKDF-SHA256, AES-256-GCM |
| Packaging | Docker Engine and Docker Compose | FastAPI and Granite services on LinuxONE s390x |
| Native math/build | OpenBLAS, LAPACK, GCC/G++, gfortran, CMake, pkg-config, Rust/Cargo | Scientific/PQC builds and model-server runtime |
| HTTP/config | httpx, python-dotenv | Supabase/model requests and local configuration |

## Versions observed in the tested application image

| Component | Version |
|---|---|
| Python image | `python:3.11-slim-trixie` |
| scikit-learn | `1.4.1.post1` (pinned to saved estimator) |
| NumPy | `1.26.4` (pinned) |
| SciPy | `1.17.1` (observed build, not pinned) |
| joblib | `1.6.0` (observed build, not pinned) |
| liboqs / Python bindings | `0.16.0` / `0.16.0.1` |
| FastAPI / Uvicorn | `0.144.0` / `0.54.0` (observed build) |
| Supabase SDK | `2.33.0` (observed build) |
| cryptography | `50.0.2` (observed build) |

The host development environment used Python 3.12; the application container uses Python 3.11. Model loading and `predict_proba` passed in the pinned container environment. This does not reproduce the full training environment or prove predictive accuracy. Some dependencies remain unpinned; save a final package inventory before submission.

## Model configuration

- Predictor: `backend/model/recommender.joblib`, trained with `evaluation/train_recommender.py` on synthetic orders.
- Generator: `ibm-granite/granite-4.2-3b-GGUF`, `granite-4.2-3b-Q4_K_M.gguf`, source path revision `c40945d` in Compose.
- On s390x, Compose converts weights to big endian with llama.cpp's `gguf_convert_endian.py` and caches the result in a named volume.
- Granite alias: `granite`; private API: `http://granite:8080/v1`.
- llama.cpp currently clones its default branch, not a fixed commit. Record/pin the actual build revision for reproducibility.

## Legacy material

`backend/schema.sql` is the SQLite schema used by the synthetic-data generator; it is not the live application schema. `requirements-dev.txt` describes evaluation dependencies. `requirements-ai.txt` contains earlier candidates, including llama-cpp-python; the deployed generator uses standalone llama-server, not that Python binding. `argon2-cffi` remains in requirements but is not the application's password implementation. Do not list these unused candidates as completed integrations.

`tests/test_role_boundaries.py` still assumes old SQLite sessions and must be updated before it is used as a current regression suite. See [security evidence](SECURITY_EVIDENCE.md).
