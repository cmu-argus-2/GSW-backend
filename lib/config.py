"""
Application Configuration Module
--------------------------------
This file defines runtime configuration parameters for the system,
including network endpoints, authentication settings, and radio frequency.

The configuration is primarily controlled via environment variables
(e.g., AUTH_KEY) and static defaults defined below.
"""

import os

# ============================================================
# Runtime Mode
# ============================================================

MODE = "DBG"  # Options: DBG (debug), PROD (production), etc.


# ============================================================
# Authentication
# ============================================================

# Command authentication key (expected: 32 hex characters)
AUTH_KEY = os.getenv("AUTH_KEY")
if AUTH_KEY is None:
    raise ValueError("AUTH_KEY is not set")


# ============================================================
# Network Configuration
# ============================================================

COMMAND_INTERFACE_IP = "0.0.0.0"
COMMAND_INTERFACE_PORT = 8000

INGEST_GATEWAY_IP = "172.20.48.220"
INGEST_GATEWAY_PORT = 5555


# ============================================================
# Radio Configuration
# ============================================================

ARGUS_FREQ = 433.707  # MHz


# ============================================================
# Pretty Print Configuration
# ============================================================

def _mask_key(key: str, visible: int = 4) -> str:
    """Return masked version of key showing only first/last characters."""
    if len(key) <= visible * 2:
        return "*" * len(key)
    return f"{key[:visible]}...{key[-visible:]}"


print("\n" + "=" * 55)
print("APPLICATION CONFIGURATION")
print("=" * 55)

print(f"Mode                : {MODE}")
print(f"Auth Key            : {_mask_key(AUTH_KEY)}")

print("\n[Command Interface]")
print(f"  Address           : {COMMAND_INTERFACE_IP}")
print(f"  Port              : {COMMAND_INTERFACE_PORT}")

print("\n[Ingest Gateway]")
print(f"  Address           : {INGEST_GATEWAY_IP}")
print(f"  Port              : {INGEST_GATEWAY_PORT}")

print("\n[Radio]")
print(f"  ARGUS Frequency   : {ARGUS_FREQ:.3f} MHz")

print("=" * 55 + "\n")
