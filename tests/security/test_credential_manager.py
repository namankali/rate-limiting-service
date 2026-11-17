import base64
import re
import secrets

import pytest
from app.security.credential_manager import CredentialManager


@pytest.fixture
def hmac_key() -> bytes:
    return secrets.token_bytes(32)


def test_generate_credential_id():
    credential_id = CredentialManager.generate_credential_id()
    pattern = r"^[0-9a-z]{32}$"
    regex_match = bool(re.fullmatch(pattern=pattern, string=credential_id))

    assert len(credential_id) == 32
    assert regex_match is True


def test_generate_secret():
    secret = CredentialManager.generate_secret()

    restored_padding = "=" * (-len(secret) % 4)
    secret += restored_padding

    restored_secret = base64.urlsafe_b64decode(secret)

    assert isinstance(secret, str)
    assert len(restored_secret) == 32
    assert isinstance(restored_secret, bytes)


def test_generate_credential():
    credential = CredentialManager.generate_credential()

    credential_id, secret = credential.split(":", 1)

    restored_padding = "=" * (-len(secret) % 4)
    decoded_secret = base64.urlsafe_b64decode(secret + restored_padding)

    assert isinstance(credential, str)
    assert re.fullmatch(r"[0-9a-f]{32}", credential_id)
    assert isinstance(decoded_secret, bytes)
    assert len(decoded_secret) == 32


def test_generate_verifier(hmac_key):
    secret = CredentialManager.generate_secret()

    generated_verifier = CredentialManager.generate_verifier(hmac_key=hmac_key, secret=secret)

    generated_verifier_2 = CredentialManager.generate_verifier(hmac_key=hmac_key, secret=secret)

    assert isinstance(generated_verifier, bytes)
    assert len(generated_verifier) == 32
    assert generated_verifier == generated_verifier_2


def test_verify_credentials(hmac_key):
    secret = CredentialManager.generate_secret()
    generated_verifier = CredentialManager.generate_verifier(hmac_key=hmac_key, secret=secret)

    verified_credential = CredentialManager.verify_credential(
        secret=secret, hmac_key=hmac_key, stored_verifier=generated_verifier
    )

    assert verified_credential is True


def test_verify_credential_invalid_secret(hmac_key):
    secret = CredentialManager.generate_secret()
    verifier = CredentialManager.generate_verifier(secret=secret, hmac_key=hmac_key)

    secret_2 = CredentialManager.generate_secret()

    verify_credential = CredentialManager.verify_credential(
        hmac_key=hmac_key, secret=secret_2, stored_verifier=verifier
    )

    assert verify_credential is False
