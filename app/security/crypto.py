import base64
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from config import settings

ENCRYPTION_KEY = base64.b64decode(settings.ENCRYPTION_KEY)


def encrypt_session(data: str) -> str:
    """
    Encrypt the session data using the encryption key.
    Args:
        data (str): The session data to encrypt.
    """
    iv = os.urandom(12)
    cipher = Cipher(algorithms.AES(ENCRYPTION_KEY), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(data.encode()) + encryptor.finalize()
    tag = encryptor.tag

    # Encode the ciphertext, iv, and tag in base64 with `:` as a separator
    return f"{base64.b64encode(ciphertext).decode()}:{base64.b64encode(iv).decode()}:{base64.b64encode(tag).decode()}"  # NOQA


def decrypt_session(encrypted_data: str) -> str:
    """
    Decrypt the session data using the encryption key.
    Args:
        encrypted_data (str): The encrypted session data in the format
                              "ciphertext:iv:tag" where each part is base64 encoded.
    """
    if encrypted_data == "":
        return encrypted_data

    try:
        ciphertext, iv, tag = map(base64.b64decode, encrypted_data.split(":"))
    except ValueError as e:
        raise Exception("Invalid encrypted data format.") from e

    cipher = Cipher(algorithms.AES(ENCRYPTION_KEY), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()

    return decrypted_data.decode()
