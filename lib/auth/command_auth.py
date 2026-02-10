import hmac
import hashlib
import os

def compute_mac(key: bytes, command_id: int, args_bytes: bytes, nonce: bytes) -> bytes:
    """
    Compute HMAC-SHA256 MAC for command authentication.

    Args:
        key: Shared secret key between GS and spacecraft
        command_id: Command message ID (1 byte)
        args_bytes: Serialized command arguments
        nonce: Freshness parameter (e.g. counter or random)

    Returns:
        bytes: 32-byte MAC
    """
    message = (command_id.to_bytes(1, "big") + args_bytes + nonce)

    return hmac.new(key, message, hashlib.sha256).digest()

def get_next_nonce() -> bytes:
    """
    Get the next nonce for command authentication.

    Returns:
        bytes: 4-byte nonce
    """
    return os.urandom(4)