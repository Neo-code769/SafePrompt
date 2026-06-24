import pytest

from crypto import decrypt_mapping, encrypt_mapping, is_encrypted

SAMPLE = {
    "mapping": {"jean.dupont@acme.fr": "[EMAIL_1]"},
    "reverse_mapping": {"[EMAIL_1]": "jean.dupont@acme.fr"},
}


def test_encrypt_produces_encrypted_flag():
    enc = encrypt_mapping(SAMPLE, "motdepasse")
    assert enc["encrypted"] is True
    assert "ciphertext" in enc
    assert "salt" in enc
    assert "nonce" in enc


def test_roundtrip():
    pw = "S3cr3t!2024"
    enc = encrypt_mapping(SAMPLE, pw)
    dec = decrypt_mapping(enc, pw)
    assert dec["mapping"] == SAMPLE["mapping"]


def test_wrong_password_raises():
    enc = encrypt_mapping(SAMPLE, "bon_mdp")
    with pytest.raises(Exception):
        decrypt_mapping(enc, "mauvais_mdp")


def test_is_encrypted():
    enc = encrypt_mapping(SAMPLE, "x")
    assert is_encrypted(enc) is True
    assert is_encrypted(SAMPLE) is False


def test_different_ciphertext_each_call():
    enc1 = encrypt_mapping(SAMPLE, "pw")
    enc2 = encrypt_mapping(SAMPLE, "pw")
    assert enc1["ciphertext"] != enc2["ciphertext"]  # sel + nonce aléatoires
