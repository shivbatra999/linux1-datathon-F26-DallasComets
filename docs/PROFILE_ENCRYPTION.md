# Customer profile encryption

## Scope and flow

The customer form accepts name, phone, and address. The authorized backend encrypts this JSON before writing `profiles.encrypted_profile` and decrypts it only for the signed-in customer.

ML-KEM-768 establishes a fresh shared secret; HKDF-SHA256 derives a 32-byte AES key; AES-256-GCM encrypts and authenticates the JSON with a fresh salt and nonce. AAD includes the customer UUID and version. Each save produces a new encapsulation/ciphertext.

The envelope contains version, key_id, algorithm, kem_ciphertext, salt, nonce, and ciphertext. Binary values use base64. The private key is not part of the envelope.

This helper does not encrypt login passwords, email, database identifiers, order records, or transport. Supabase Auth manages credentials. Standard HTTPS/SSH protects network connections. This is PQC-assisted profile encryption, not quantum-safe TLS or a production cryptography certification.

## Existing deployment keys

The backend reads:

- `~/.config/simplecater/keys/profile-v1.public`
- `~/.config/simplecater/keys/profile-v1.secret`

Directory permissions: 700; both files: 600. Existing Supabase ciphertext requires the corresponding existing secret key. Do not regenerate or replace it. Keep a secure recoverable backup outside Git/Supabase/model inputs. Version identification exists, but key rotation/multiple key versions are not implemented.

Docker mounts the host key directory read-only at `/home/app/.config/simplecater/keys`. UID 1000 in the image matches the tested host. Read-only mounting protects files from writes by the container; a compromised authorized backend could still read them.

## Native setup for direct Python execution

The container builds liboqs itself. Host Python development requires a native installation:

```bash
sudo apt install build-essential cmake libssl-dev git
mkdir -p "$HOME/.local/src"
git clone --depth 1 --branch 0.16.0 https://github.com/open-quantum-safe/liboqs.git "$HOME/.local/src/liboqs-0.16.0"
cmake -S "$HOME/.local/src/liboqs-0.16.0" -B "$HOME/.local/src/liboqs-0.16.0/build" \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON -DOQS_BUILD_ONLY_LIB=ON \
  -DOQS_MINIMAL_BUILD=KEM_ml_kem_768 -DCMAKE_INSTALL_PREFIX="$HOME/.local/liboqs" \
  -DCMAKE_INSTALL_LIBDIR=lib
cmake --build "$HOME/.local/src/liboqs-0.16.0/build" --parallel 2
cmake --install "$HOME/.local/src/liboqs-0.16.0/build"
export OQS_INSTALL_PATH="$HOME/.local/liboqs"
export LD_LIBRARY_PATH="$OQS_INSTALL_PATH/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
python -m pip install 'liboqs-python==0.16.0.1'
```

Skip cloning if the source directory already exists. Set the environment in each server terminal before using the library; the host path is not automatically available in containers.

## New isolated development keys only

Run the following only for a new test environment with separate test data, using Python with liboqs installed. Never use it to replace an existing deployment's keys:

```python
from pathlib import Path
import os
import oqs

folder = Path.home() / ".config/simplecater/keys"
folder.mkdir(parents=True, exist_ok=True, mode=0o700)
folder.chmod(0o700)
public = folder / "profile-v1.public"
secret = folder / "profile-v1.secret"
if public.exists() or secret.exists():
    raise SystemExit("Existing keys found; nothing overwritten.")
with oqs.KeyEncapsulation("ML-KEM-768") as kem:
    public_bytes = kem.generate_keypair()
    secret_bytes = kem.export_secret_key()
for path, data in ((secret, secret_bytes), (public, public_bytes)):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
```

## Database access

Migration 002 grants authenticated users UPDATE of only `encrypted_profile`, with a customer/own-row UPDATE policy. An own-row SELECT policy, existing RLS, and appropriate grants are prerequisites. Role, business_id, and id are not editable through the profile endpoint or that column grant. Broader pre-existing policies/grants must be audited separately.

## Verification

The team reported successful ML-KEM round-trip, profile round-trip, tamper/wrong-user rejection, fresh ciphertext per save, API/browser persistence, and decryption after process/container restarts. The database screenshot showed an encryption envelope, and API reads recovered the expected test values. This evidence is scoped to those checks, not a complete penetration test. See [security evidence](SECURITY_EVIDENCE.md).
