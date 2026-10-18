# Resources and attribution

List actual retained resources in the final submission. URLs below are upstream sources, not a claim that all projects share a license. Preserve required notices and check the exact release/model terms before redistribution. The application repository has no project LICENSE file at this documentation checkpoint; choose a license deliberately rather than implying one.

## Runtime software

| Resource | Use | Upstream |
|---|---|---|
| Python | Backend language and standard library | https://www.python.org/ |
| FastAPI | APIs, page routing, middleware | https://github.com/fastapi/fastapi |
| Starlette | ASGI middleware/responses and test client | https://github.com/Kludex/starlette |
| Pydantic | Input validation | https://github.com/pydantic/pydantic |
| Uvicorn | Application server | https://github.com/Kludex/uvicorn |
| Supabase Python SDK | Auth and PostgREST integration | https://github.com/supabase/supabase-py |
| Supabase / PostgreSQL / PostgREST | Hosted identity/database service and underlying open-source components | https://github.com/supabase/supabase ; https://www.postgresql.org/ ; https://github.com/PostgREST/postgrest |
| httpx | HTTP requests and tests | https://github.com/encode/httpx |
| python-dotenv | Environment loading | https://github.com/theskumar/python-dotenv |
| scikit-learn | BernoulliNB predictive model | https://github.com/scikit-learn/scikit-learn |
| NumPy / SciPy | Numeric arrays and scientific model dependencies | https://github.com/numpy/numpy ; https://github.com/scipy/scipy |
| joblib / threadpoolctl | Model persistence and numeric runtime support | https://github.com/joblib/joblib ; https://github.com/joblib/threadpoolctl |
| cryptography | HKDF-SHA256 and AES-GCM | https://github.com/pyca/cryptography |
| liboqs / liboqs-python | ML-KEM-768 native implementation and bindings | https://github.com/open-quantum-safe/liboqs ; https://github.com/open-quantum-safe/liboqs-python |
| llama.cpp | llama-server inference and GGUF endian conversion | https://github.com/ggml-org/llama.cpp |
| OpenBLAS / LAPACK | Native math libraries | https://github.com/OpenMathLib/OpenBLAS ; https://github.com/Reference-LAPACK/lapack |
| Docker/Moby / Compose | Tested container runtime and service definition | https://github.com/moby/moby ; https://github.com/docker/compose |
| Python and Ubuntu container images | Build/runtime bases | https://hub.docker.com/_/python ; https://hub.docker.com/_/ubuntu |
| Git, CMake, GCC/gfortran, Rust/Cargo, pkg-config | Source builds and dependency tooling | https://git-scm.com/ ; https://cmake.org/ ; https://gcc.gnu.org/ ; https://www.rust-lang.org/ ; https://www.freedesktop.org/wiki/Software/pkg-config/ |

Supabase's hosted service is an external service, not software running on LinuxONE. Transitive packages and distribution libraries also need to be included in the final image inventory/notices where applicable.

## Model and evaluation

- IBM Granite weights: https://huggingface.co/ibm-granite/granite-4.2-3b-GGUF . Current Compose uses revision path `c40945d`, quantization `Q4_K_M`, then converts the file to big endian for s390x. Verify the model card/license and record exact source/hash before final redistribution.
- Predictive artifact: `backend/model/recommender.joblib`, created by team training code using scikit-learn. Training data is synthetic, produced by `evaluation/seed_synthetic.py`; it is not an external customer dataset.
- Faker: synthetic data generation, https://github.com/joke2k/faker . Matplotlib/Pillow: evaluation graphics, https://github.com/matplotlib/matplotlib and https://github.com/python-pillow/Pillow . SQLite: local synthetic training database only, https://www.sqlite.org/ . None is the live application datastore.
- IBM learning material: https://github.com/linuxone-community-cloud/jupyter-lab-ml . State any specific adapted files and preserve their notices; do not represent unchanged reference notebooks as team-original solution code.
- Evaluation JSON uses synthetic order-grouped folds; describe the dataset and baseline honestly. See [security evidence](SECURITY_EVIDENCE.md).

## Interface assets and infrastructure

- DM Sans and Manrope fonts: https://fonts.google.com/specimen/DM+Sans and https://fonts.google.com/specimen/Manrope . Follow the font distribution licenses.
- Unsplash remote images: photo IDs are in frontend fixtures/styles and the catalog adapter. Image terms are separate from software licensing: https://unsplash.com/license . Photos are illustrative, not proof of actual menu appearance.
- GitHub Actions deployment uses https://github.com/appleboy/ssh-action at `v1.2.0` to update the server checkout over SSH.
- IBM LinuxONE Community Cloud: hosting platform, not an application dependency license. Follow the instance terms and event guidance.

## Do not claim as deployed

llama-cpp-python is a legacy candidate in requirements-ai.txt; deployed generation uses llama-server. Argon2-cffi remains installed but custom password hashing is not the login implementation. Podman was an alternative, while the reported deployment uses Docker. Granite 3.3 2B was an early candidate; the current model is Granite 4.2 3B. No Telum accelerator use has been demonstrated.

## Final attribution checklist

Record package versions with `python -m pip freeze` inside the tested container; record native/container/llama.cpp/model revisions separately. Pin moving references after validation. Preserve required licenses for redistributed binaries, fonts, or weights. Confirm organizers' disclosure requirements for AI-assisted development and third-party resources.
