"""Encrypt customer profiles before storing them in Supabase."""
import base64
import json
import importlib
import os
from pathlib import Path
from uuid import UUID

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

KEY_DIR = Path.home() / ".config" / "simplecater" / "keys"
ALGORITHM = "ML-KEM-768+HKDF-SHA256+AES-256-GCM"


def _oqs():
    try:
        return importlib.import_module("oqs")
    except (FileNotFoundError, ImportError, RuntimeError) as error:
        raise RuntimeError(
            "Profile encryption requires the liboqs native library."
        ) from error


def encode(value):
    return base64.b64encode(value).decode("ascii")


def decode(value):
    return base64.b64decode(value, validate=True)


def context(user_id):
    return ("simplecater:profile:v1:" + str(UUID(str(user_id)))).encode()


def derive_key(secret, salt):
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=b"simplecater-profile-v1",
    ).derive(secret)


def encrypt_profile(user_id, profile):
    aad = context(user_id)
    plaintext = json.dumps(profile, allow_nan=False).encode()
    if len(plaintext) > 16384:
        raise ValueError("Profile is too large.")

    public_key = (KEY_DIR / "profile-v1.public").read_bytes()
    with _oqs().KeyEncapsulation("ML-KEM-768") as kem:
        encapsulated, secret = kem.encap_secret(public_key)

    salt = os.urandom(32)
    nonce = os.urandom(12)
    ciphertext = AESGCM(derive_key(secret, salt)).encrypt(
        nonce, plaintext, aad
    )

    return {
        "version": 1,
        "key_id": "profile-v1",
        "algorithm": ALGORITHM,
        "kem_ciphertext": encode(encapsulated),
        "salt": encode(salt),
        "nonce": encode(nonce),
        "ciphertext": encode(ciphertext),
    }


def decrypt_profile(user_id, envelope):
    if (
        envelope.get("version") != 1
        or envelope.get("key_id") != "profile-v1"
        or envelope.get("algorithm") != ALGORITHM
    ):
        raise ValueError("Unsupported encrypted profile.")

    aad = context(user_id)
    secret_key = (KEY_DIR / "profile-v1.secret").read_bytes()
    with _oqs().KeyEncapsulation("ML-KEM-768", secret_key) as kem:
        secret = kem.decap_secret(decode(envelope["kem_ciphertext"]))

    plaintext = AESGCM(
        derive_key(secret, decode(envelope["salt"]))
    ).decrypt(
        decode(envelope["nonce"]),
        decode(envelope["ciphertext"]),
        aad,
    )
    return json.loads(plaintext)
