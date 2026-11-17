import base64
import hashlib
import hmac
from secrets import token_bytes, token_hex


class CredentialManager:
    @staticmethod
    def generate_credential_id() -> str:
        return token_hex(16)

    @staticmethod
    def generate_secret() -> str:
        secret_bytes = token_bytes(32)

        encoded_secret = base64.urlsafe_b64encode(secret_bytes).decode("ascii")
        return encoded_secret.rstrip("=")

    @staticmethod
    def generate_credential() -> str:
        credential_id = CredentialManager.generate_credential_id()
        secret = CredentialManager.generate_secret()

        return f"{credential_id}:{secret}"

    @staticmethod
    def generate_verifier(hmac_key: bytes, secret: str) -> bytes:
        return hmac.digest(hmac_key, secret.encode("utf-8"), hashlib.sha256)

    @staticmethod
    def verify_credential(secret: str, hmac_key: bytes, stored_verifier: bytes) -> bool:
        generated_verifier = CredentialManager.generate_verifier(hmac_key=hmac_key, secret=secret)

        return hmac.compare_digest(generated_verifier, stored_verifier)
