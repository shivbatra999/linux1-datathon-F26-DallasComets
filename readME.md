# SimpleCater on LinuxONE

> A secure, AI-assisted catering platform designed for IBM LinuxONE and s390x environments.

SimpleCater is the Dallas Comets team's submission for the IBM Z × Datathon Fall 2026. The project provides separate customer and business-owner experiences for browsing catering menus, receiving item recommendations, managing orders, protecting customer profiles, and generating business-oriented summaries from verified order data.

The application is designed around a small, auditable deployment model: one FastAPI service, one primary data store, local predictive and generative inference, and containerized execution on LinuxONE.

## Team

- **Shivansh Batra**
- **Arman Sarder**
- **Eshwar Singh Rajaputana**
- **MUHD Ayman Haque**

## Project Goals

SimpleCater focuses on four core goals:

1. **Provide role-specific workflows** for customers and business owners.
2. **Use AI responsibly** by giving models only the minimum data needed for recommendations and summaries.
3. **Protect sensitive customer information** through authenticated access, encrypted profile storage, and strict ownership checks.
4. **Demonstrate LinuxONE readiness** through s390x-compatible container builds and local inference services.

## Key Capabilities

### Customer experience

- Sign in through a customer-specific workspace.
- Browse available menu items.
- Receive item-pairing recommendations with supporting explanations.
- Build a cart and submit orders using server-controlled pricing.
- View personal order history.
- View and update a personal profile.

### Business-owner experience

- Sign in through a separate owner workspace.
- Review orders belonging to the owner's business.
- View aggregate sales and order information.
- Request AI-assisted business summaries grounded in verified backend data.

### Security and privacy

- Session-based authentication with role-aware route protection.
- Customer and owner workspaces are isolated from one another.
- Orders and business data are intended to be scoped by authenticated ownership, not by client-provided identifiers.
- Customer profile data can be encrypted before storage using ML-KEM-768 key establishment, HKDF-SHA-256 key derivation, and AES-256-GCM authenticated encryption.
- Decrypted profiles, credentials, encryption keys, and unrelated personal information are excluded from AI inputs.
- Unsafe API requests require a trusted request origin, and HTTP responses include no-store and MIME-sniffing protections.

## High-Level Architecture

```text
Browser
  │
  ├── Customer workspace
  └── Owner workspace
          │
          ▼
FastAPI application on LinuxONE
  │
  ├── Authentication and session validation
  ├── Role and resource-ownership checks
  ├── Catalog, cart, checkout, and order APIs
  ├── Profile encryption/decryption workflow
  ├── Predictive recommendation service
  └── Grounded local generative summaries
          │
          ├── Supabase-backed application data
          ├── Persistent application storage
          └── Local Granite inference service
```

The application separates verified computation from language generation. The backend calculates and validates totals, counts, and predictive results first. The generative model receives only permitted, structured facts and produces a readable explanation; it is not responsible for authorization, database access, pricing, or mutation of application state.

## Technology Stack

| Area | Technology |
| --- | --- |
| Backend API | Python, FastAPI, Uvicorn |
| Frontend | HTML, CSS, JavaScript modules, Fetch API |
| Data and authentication integration | Supabase |
| Password/security utilities | Argon2, Python secrets, cryptographic helpers |
| Profile encryption | liboqs / ML-KEM-768, HKDF-SHA-256, AES-256-GCM |
| Predictive analytics | scikit-learn, NumPy, joblib |
| Local generative inference | IBM Granite-compatible GGUF model through `llama-server` |
| Packaging and deployment | Docker, Docker Compose, LinuxONE s390x |
| Native acceleration | OpenBLAS and LinuxONE-compatible compiler settings |

For additional implementation details, see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/TECH_STACK.md`](docs/TECH_STACK.md), [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md), [`docs/PROFILE_ENCRYPTION.md`](docs/PROFILE_ENCRYPTION.md), and [`docs/OPEN_SOURCE_RESOURCES.md`](docs/OPEN_SOURCE_RESOURCES.md).

## Repository Structure

```text
.
├── backend/                 # FastAPI application and backend services
├── frontend/                # Customer and owner browser interfaces
├── docker/granite/          # LinuxONE-compatible Granite inference image
├── docs/                    # Architecture, API, security, and planning documents
├── supabase/                # Database migrations and Supabase configuration
├── tests/                   # Automated and integration tests
├── Dockerfile               # Core application image
├── compose.yaml             # Application plus local Granite service
├── compose.encryption.yaml  # Encryption-focused deployment configuration
├── requirements.txt         # Runtime Python dependencies
└── .env.example             # Required environment-variable template
```

## Prerequisites

For the intended deployment, use an IBM LinuxONE environment running the s390x architecture with Docker Engine and Docker Compose, or a compatible Podman setup. You will also need access to the required Supabase project, network access for build dependencies and the Granite model, persistent storage for application data and models, and existing profile-encryption keys when using the encryption deployment.

The Granite image explicitly targets `linux/s390x` and compiles `llama-server` with LinuxONE-compatible settings.

## Configuration

Create a local `.env` file from the example:

```bash
cp .env.example .env
```

Set the required values before starting the application:

```dotenv
SUPABASE_URL=your-supabase-project-url
SUPABASE_PUBLISHABLE_KEY=your-supabase-publishable-key
SIMPLECATER_ORIGIN=http://127.0.0.1:8000
SIMPLECATER_LLM_URL=http://granite:8080/v1
SIMPLECATER_LLM_MODEL=granite
SIMPLECATER_LLM_TIMEOUT_SECONDS=180
SIMPLECATER_LLM_REASONING_FORMAT=none
```

Never commit `.env`, private encryption keys, model credentials, or other secrets to the repository.

## Run with Docker Compose

From the repository root:

```bash
docker compose up -d --build
```

This starts the SimpleCater application on `http://127.0.0.1:8000` and the local Granite inference service on port `8080`.

Check application health with:

```bash
curl http://127.0.0.1:8000/health
```

Stop the deployment with:

```bash
docker compose down
```

The Compose configuration uses named volumes for application data and downloaded Granite model files so these resources can persist across container restarts.

## Run the Backend Without Containers

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

The backend serves the frontend and exposes the application API at `/api`.

The `liboqs-python` dependency also requires the native `liboqs` library. Follow [`docs/PROFILE_ENCRYPTION.md`](docs/PROFILE_ENCRYPTION.md) for LinuxONE installation, key-management, and verification guidance.

## Frontend-Only Preview

```bash
cd frontend
python3 -m http.server 4319
```

Open `http://127.0.0.1:4319/index.html` in a browser. The preview includes simulated demo sessions for the customer and owner interfaces. Demo mode is intended for UI review only and is **not** a security boundary or production authentication system.

## Current Implementation Status

The repository contains the core application structure, role-guarded FastAPI shell, frontend workspaces, Docker build definitions, Compose deployments, security documentation, and integration points for predictive and generative AI.

Some business and model workflows are still being integrated. Verify catalog, checkout, order, authentication, model, and Supabase integrations before treating the repository as production-ready. The backend intentionally returns `501 Not Implemented` for unfinished integration routes rather than simulating completed behavior.

Before a final LinuxONE demonstration, validate end-to-end authentication, role boundaries, server-side pricing, order ownership, predictive results, grounded AI summaries, profile encryption, key persistence, container restarts, HTTPS, and secrets management.

## Responsible AI and Data Boundaries

SimpleCater treats AI as an assistive layer rather than a source of truth:

- Recommendations should be accompanied by evidence or an explanation.
- Business summaries should be generated from backend-verified aggregates.
- Models should not receive customer profiles, passwords, session tokens, or encryption keys.
- Models should not access SQLite, Supabase, the filesystem, or operating-system commands.
- Pricing, authorization, order creation, and data mutation remain deterministic backend responsibilities.

## License and Third-Party Components

This project was created for the IBM Z × Datathon Fall 2026. Review [`docs/OPEN_SOURCE_RESOURCES.md`](docs/OPEN_SOURCE_RESOURCES.md) for third-party components, model resources, and attribution requirements before redistribution or public deployment.

---

**SimpleCater** — secure catering workflows and responsible local AI on IBM LinuxONE.# SimpleCater on LinuxONE

> A secure, AI-assisted catering platform designed for IBM LinuxONE and s390x environments.

SimpleCater is the Dallas Comets team's submission for the IBM Z × Datathon Fall 2026. The project provides separate customer and business-owner experiences for browsing catering menus, receiving item recommendations, managing orders, protecting customer profiles, and generating business-oriented summaries from verified order data.

The application is designed around a small, auditable deployment model: one FastAPI service, one primary data store, local predictive and generative inference, and containerized execution on LinuxONE.

## Team

- **Shivansh Batra**
- **Arman Sarder**
- **Eshwar Singh Rajaputana**
- **MUHD Ayman Haque**

## Project Goals

SimpleCater focuses on four core goals:

1. **Provide role-specific workflows** for customers and business owners.
2. **Use AI responsibly** by giving models only the minimum data needed for recommendations and summaries.
3. **Protect sensitive customer information** through authenticated access, encrypted profile storage, and strict ownership checks.
4. **Demonstrate LinuxONE readiness** through s390x-compatible container builds and local inference services.

## Key Capabilities

### Customer experience

- Sign in through a customer-specific workspace.
- Browse available menu items.
- Receive item-pairing recommendations with supporting explanations.
- Build a cart and submit orders using server-controlled pricing.
- View personal order history.
- View and update a personal profile.

### Business-owner experience

- Sign in through a separate owner workspace.
- Review orders belonging to the owner's business.
- View aggregate sales and order information.
- Request AI-assisted business summaries grounded in verified backend data.

### Security and privacy

- Session-based authentication with role-aware route protection.
- Customer and owner workspaces are isolated from one another.
- Orders and business data are intended to be scoped by authenticated ownership, not by client-provided identifiers.
- Customer profile data can be encrypted before storage using ML-KEM-768 key establishment, HKDF-SHA-256 key derivation, and AES-256-GCM authenticated encryption.
- Decrypted profiles, credentials, encryption keys, and unrelated personal information are excluded from AI inputs.
- Unsafe API requests require a trusted request origin, and HTTP responses include no-store and MIME-sniffing protections.

## High-Level Architecture

```text
Browser
  │
  ├── Customer workspace
  └── Owner workspace
          │
          ▼
FastAPI application on LinuxONE
  │
  ├── Authentication and session validation
  ├── Role and resource-ownership checks
  ├── Catalog, cart, checkout, and order APIs
  ├── Profile encryption/decryption workflow
  ├── Predictive recommendation service
  └── Grounded local generative summaries
          │
          ├── Supabase-backed application data
          ├── Persistent application storage
          └── Local Granite inference service
```

The application separates verified computation from language generation. The backend calculates and validates totals, counts, and predictive results first. The generative model receives only permitted, structured facts and produces a readable explanation; it is not responsible for authorization, database access, pricing, or mutation of application state.

## Technology Stack

| Area | Technology |
| --- | --- |
| Backend API | Python, FastAPI, Uvicorn |
| Frontend | HTML, CSS, JavaScript modules, Fetch API |
| Data and authentication integration | Supabase |
| Password/security utilities | Argon2, Python secrets, cryptographic helpers |
| Profile encryption | liboqs / ML-KEM-768, HKDF-SHA-256, AES-256-GCM |
| Predictive analytics | scikit-learn, NumPy, joblib |
| Local generative inference | IBM Granite-compatible GGUF model through `llama-server` |
| Packaging and deployment | Docker, Docker Compose, LinuxONE s390x |
| Native acceleration | OpenBLAS and LinuxONE-compatible compiler settings |

For additional implementation details, see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/TECH_STACK.md`](docs/TECH_STACK.md), [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md), [`docs/PROFILE_ENCRYPTION.md`](docs/PROFILE_ENCRYPTION.md), and [`docs/OPEN_SOURCE_RESOURCES.md`](docs/OPEN_SOURCE_RESOURCES.md).

## Repository Structure

```text
.
├── backend/                 # FastAPI application and backend services
├── frontend/                # Customer and owner browser interfaces
├── docker/granite/          # LinuxONE-compatible Granite inference image
├── docs/                    # Architecture, API, security, and planning documents
├── supabase/                # Database migrations and Supabase configuration
├── tests/                   # Automated and integration tests
├── Dockerfile               # Core application image
├── compose.yaml             # Application plus local Granite service
├── compose.encryption.yaml  # Encryption-focused deployment configuration
├── requirements.txt         # Runtime Python dependencies
└── .env.example             # Required environment-variable template
```

## Prerequisites

For the intended deployment, use an IBM LinuxONE environment running the s390x architecture with Docker Engine and Docker Compose, or a compatible Podman setup. You will also need access to the required Supabase project, network access for build dependencies and the Granite model, persistent storage for application data and models, and existing profile-encryption keys when using the encryption deployment.

The Granite image explicitly targets `linux/s390x` and compiles `llama-server` with LinuxONE-compatible settings.

## Configuration

Create a local `.env` file from the example:

```bash
cp .env.example .env
```

Set the required values before starting the application:

```dotenv
SUPABASE_URL=your-supabase-project-url
SUPABASE_PUBLISHABLE_KEY=your-supabase-publishable-key
SIMPLECATER_ORIGIN=http://127.0.0.1:8000
SIMPLECATER_LLM_URL=http://granite:8080/v1
SIMPLECATER_LLM_MODEL=granite
SIMPLECATER_LLM_TIMEOUT_SECONDS=180
SIMPLECATER_LLM_REASONING_FORMAT=none
```

Never commit `.env`, private encryption keys, model credentials, or other secrets to the repository.

## Run with Docker Compose

From the repository root:

```bash
docker compose up -d --build
```

This starts the SimpleCater application on `http://127.0.0.1:8000` and the local Granite inference service on port `8080`.

Check application health with:

```bash
curl http://127.0.0.1:8000/health
```

Stop the deployment with:

```bash
docker compose down
```

The Compose configuration uses named volumes for application data and downloaded Granite model files so these resources can persist across container restarts.

## Run the Backend Without Containers

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

The backend serves the frontend and exposes the application API at `/api`.

The `liboqs-python` dependency also requires the native `liboqs` library. Follow [`docs/PROFILE_ENCRYPTION.md`](docs/PROFILE_ENCRYPTION.md) for LinuxONE installation, key-management, and verification guidance.

## Frontend-Only Preview

```bash
cd frontend
python3 -m http.server 4319
```

Open `http://127.0.0.1:4319/index.html` in a browser. The preview includes simulated demo sessions for the customer and owner interfaces. Demo mode is intended for UI review only and is **not** a security boundary or production authentication system.

## Current Implementation Status

The repository contains the core application structure, role-guarded FastAPI shell, frontend workspaces, Docker build definitions, Compose deployments, security documentation, and integration points for predictive and generative AI.

Some business and model workflows are still being integrated. Verify catalog, checkout, order, authentication, model, and Supabase integrations before treating the repository as production-ready. The backend intentionally returns `501 Not Implemented` for unfinished integration routes rather than simulating completed behavior.

Before a final LinuxONE demonstration, validate end-to-end authentication, role boundaries, server-side pricing, order ownership, predictive results, grounded AI summaries, profile encryption, key persistence, container restarts, HTTPS, and secrets management.

## Responsible AI and Data Boundaries

SimpleCater treats AI as an assistive layer rather than a source of truth:

- Recommendations should be accompanied by evidence or an explanation.
- Business summaries should be generated from backend-verified aggregates.
- Models should not receive customer profiles, passwords, session tokens, or encryption keys.
- Models should not access SQLite, Supabase, the filesystem, or operating-system commands.
- Pricing, authorization, order creation, and data mutation remain deterministic backend responsibilities.

## License and Third-Party Components

This project was created for the IBM Z × Datathon Fall 2026. Review [`docs/OPEN_SOURCE_RESOURCES.md`](docs/OPEN_SOURCE_RESOURCES.md) for third-party components, model resources, and attribution requirements before redistribution or public deployment.

---

**SimpleCater** — secure catering workflows and responsible local AI on IBM LinuxONE.
