# Customer profile encryption

## What is protected

Customer name, phone, and address are encrypted on the backend before
being saved to Supabase profiles.encrypted_profile.

Flow:
Customer form → authenticated FastAPI endpoint → encryption → Supabase.

Reading reverses this flow for the signed-in customer.

Algorithms:
- ML-KEM-768 establishes a shared secret.
- HKDF-SHA256 derives a 256-bit encryption key.
- AES-256-GCM encrypts the profile and detects tampering.
- Authenticated context binds ciphertext to the customer UUID and format version.

This feature does not encrypt login passwords, order records, or network
traffic. Supabase Auth manages passwords. HTTPS protects deployed traffic.
Do not send decrypted profiles or encryption keys to AI models.

## Python dependencies

Install requirements.txt inside the backend virtual environment.

The liboqs-python package also requires the native liboqs library.
Our LinuxONE development setup uses liboqs 0.16.0 and
liboqs-python 0.16.0.1.

## Native library setup on Ubuntu/LinuxONE

```bash
sudo apt install build-essential cmake libssl-dev git

mkdir -p "$HOME/.local/src"

git clone --depth 1 --branch 0.16.0 \
  https://github.com/open-quantum-safe/liboqs.git \
  "$HOME/.local/src/liboqs-0.16.0"

cmake \
  -S "$HOME/.local/src/liboqs-0.16.0" \
  -B "$HOME/.local/src/liboqs-0.16.0/build" \
  -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_SHARED_LIBS=ON \
  -DOQS_BUILD_ONLY_LIB=ON \
  -DOQS_MINIMAL_BUILD=KEM_ml_kem_768 \
  -DCMAKE_INSTALL_PREFIX="$HOME/.local/liboqs" \
  -DCMAKE_INSTALL_LIBDIR=lib

cmake --build "$HOME/.local/src/liboqs-0.16.0/build" --parallel 2
cmake --install "$HOME/.local/src/liboqs-0.16.0/build"
```

Skip cloning if that source directory already exists.

Before starting the backend, set:

```bash
export OQS_INSTALL_PATH="$HOME/.local/liboqs"
export LD_LIBRARY_PATH="$OQS_INSTALL_PATH/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
```

## Persistent keys

The backend expects these files under the account running the server:

- ~/.config/simplecater/keys/profile-v1.public
- ~/.config/simplecater/keys/profile-v1.secret

Directory permissions: 700. File permissions: 600.

For the existing deployment, preserve its existing keys.
Never generate replacement keys over these files.
Losing the secret key makes existing encrypted profiles unreadable.

Keep keys outside Git, Supabase, logs, frontend code, and AI inputs.
Back up the secret key securely with access restricted to authorized operators.
A separate development key pair must use separate test data.

## Database permissions

Migration:
supabase/migrations/20261018_002_profile_encryption.sql

Prerequisites:
- profiles table exists and has row-level security enabled.
- Authenticated users can SELECT only their own profile.
- Customers cannot modify role, business_id, or id.

The migration permits authenticated customers to UPDATE only the
encrypted_profile column on their own row.

## API

- GET /api/profile: returns the customer's decrypted profile.
- PUT /api/profile: accepts name, phone, and address; encrypts before saving.
- Identity comes from the validated session, not the request body.
- Additional input fields are rejected.

## Verification completed on LinuxONE

- ML-KEM shared-secret round-trip.
- Profile encryption and decryption.
- Tampered ciphertext rejected.
- Wrong customer UUID rejected.
- Fresh ciphertext generated for each save.
- API save and read.
- Decryption after server restart.
- Browser edit persisted after refresh.

## Deployment work remaining

Docker must install the native library, configure its library path, and
mount the existing key directory read-only for the container's runtime user.
Installing requirements.txt alone does not complete Docker deployment.

This is a hackathon prototype using Open Quantum Safe libraries.

## Docker support completed

This section supersedes "Deployment work remaining" above.

The root Dockerfile installs liboqs 0.16.0 and checks ML-KEM-768 support.
The Granite Dockerfile is unchanged.

compose.encryption.yaml:
- Loads Supabase settings from .env.
- Runs the app at http://127.0.0.1:8002.
- Mounts existing encryption keys read-only.
- Runs as UID 1000, matching the tested LinuxONE key owner.
- Requires checking key ownership when deploying on another host.

Start from the repository root:

```bash
docker compose -p simplecater-encryption -f compose.encryption.yaml up -d --build
```

Verified inside Docker:
- Health check, login, and logout.
- ML-KEM availability and existing key access.
- Decryption of previously saved profiles.
- Profile updates.
- Decryption after a container restart.

This configuration supports local access or SSH tunneling.
Public deployment requires HTTPS and a matching SIMPLECATER_ORIGIN.
Preserve the existing keys; never replace them during deployment.
