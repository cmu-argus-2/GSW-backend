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
    print("[ERROR] - No key provided, using default key")
    AUTH_KEY = "d6172b38acb7d2a28e21662f689d1d15ad78ccc888a9c7a78ef58cb61b0f1e32"
    


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

ARGUS_FREQ = 435  # MHz

# ============================================================
# Satellite config
# ============================================================

SC_CALLSIGN = "CT6xxx"
GS_CALLSIGN = "CSXXXX"

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

print("\n[Satellite]")
print(f"  GS          : {GS_CALLSIGN}")
print(f"  SC          : {SC_CALLSIGN}")

print("=" * 55 + "\n")
