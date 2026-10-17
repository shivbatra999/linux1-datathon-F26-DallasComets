# Resources and attribution register

Keep this file in the final submission/repository. List only resources actually retained in the finished project as used; planned entries below are not claims of completed integration. Record exact tested versions and any copied/adapted files before submission.

## Current frontend and server scaffold

| Resource | Use / source |
|---|---|
| Python | Server language and standard-library sqlite3, hashlib, secrets: https://www.python.org/ and https://docs.python.org/3/library/sqlite3.html |
| SQLite | Planned single application database; session reader uses sqlite3: https://www.sqlite.org/ |
| FastAPI | Role-guarded API and page server: https://github.com/fastapi/fastapi |
| Uvicorn | ASGI server: https://github.com/Kludex/uvicorn |
| DM Sans | Frontend typography: https://fonts.google.com/specimen/DM+Sans |
| Manrope | Frontend typography: https://fonts.google.com/specimen/Manrope |
| httpx | Development-only backend boundary tests through FastAPI TestClient: https://github.com/encode/httpx |

## Selected tools still to integrate

| Resource | Planned use / source |
|---|---|
| scikit-learn | Predictive item classifier and evaluation: https://github.com/scikit-learn/scikit-learn |
| llama.cpp | Local inference engine: https://github.com/ggml-org/llama.cpp |
| llama-cpp-python | Python model runtime: https://github.com/abetlen/llama-cpp-python |
| argon2-cffi | Argon2id password hashing: https://github.com/hynek/argon2-cffi |
| cryptography | HKDF-SHA-256 and AES-GCM: https://github.com/pyca/cryptography |
| liboqs | Native ML-KEM implementation: https://github.com/open-quantum-safe/liboqs |
| liboqs-python | Python KEM bindings: https://github.com/open-quantum-safe/liboqs-python |
| Podman OR Docker/Moby | Choose the actual container runtime used: https://github.com/containers/podman or https://github.com/moby/moby |
| Python container image | Base for Dockerfile; record tag/digest deployed: https://hub.docker.com/_/python |

Model candidate only: IBM Granite 3.3 2B Instruct, https://huggingface.co/ibm-granite/granite-3.3-2b-instruct . Once selected, add exact GGUF source/revision, quantization, conversion tool and its license. Candidate is not downloaded or connected yet.

## Referenced learning material

IBM LinuxONE JupyterLab ML lab: https://github.com/linuxone-community-cloud/jupyter-lab-ml . This informed the project environment; do not submit unchanged lab notebooks as the original project. Record any code actually adapted and preserve required notices.

## Other assets (not open-source software)

Menu photography uses Unsplash remote images; licensing is separate from software licenses: https://unsplash.com/license . Photo IDs are listed in frontend/fixtures.js and styles.css. Replace if final menu images do not match actual food. App data is team-created synthetic demonstration data; no external customer dataset is currently used.

Preserve upstream license/notice files for any redistributed code, binaries, fonts or weights. The register is not a blanket claim that all dependencies share one license. Generate exact package inventory after LinuxONE installation and add transitive/native dependencies actually distributed. Record any AI-assisted development disclosures required by the organizers.
