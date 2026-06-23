"""
Chiffrement AES-256-GCM pour mapping.json
==========================================
PBKDF2-HMAC-SHA256 (480 000 itérations) → clé 256 bits.
Sortie : JSON avec champs encrypted/salt/nonce/ciphertext en base64.
"""

import base64
import json
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

_ITERATIONS = 480_000


def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_mapping(data: dict, password: str) -> dict:
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = _derive_key(password, salt)
    plaintext = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    return {
        "encrypted": True,
        "version": 1,
        "salt": base64.b64encode(salt).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode(),
    }


def decrypt_mapping(enc: dict, password: str) -> dict:
    """Lève InvalidTag (cryptography) si mot de passe incorrect."""
    salt = base64.b64decode(enc["salt"])
    nonce = base64.b64decode(enc["nonce"])
    ciphertext = base64.b64decode(enc["ciphertext"])
    key = _derive_key(password, salt)
    plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
    return json.loads(plaintext)


def is_encrypted(data: dict) -> bool:
    return bool(data.get("encrypted"))
