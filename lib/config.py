"""
Application Configuration Module
--------------------------------
This file defines runtime configuration parameters for the system,
including network endpoints, authentication settings, and radio frequency.

The configuration is primarily controlled via environment variables
(e.g., AUTH_KEY_1, AUTH_KEY_2) and static defaults defined below.
"""

import os, argparse

# ============================================================
# Runtime Mode
# ============================================================

MODE = "DBG"  # Options: DBG (debug), PROD (production), etc.


# ============================================================
# Authentication
# ============================================================

# Per-satellite auth keys (32 hex chars each).
# Set AUTH_KEY_1 / AUTH_KEY_2 in the environment; hardcoded values are fallbacks.
SAT_AUTH_KEYS = {
    1: os.getenv("AUTH_KEY_1", "d6172b38acb7d2a28e21662f689d1d15ad78ccc888a9c7a78ef58cb61b0f1e32"),
    2: os.getenv("AUTH_KEY_2", "d6172b38acb7d2a28e21662f689d1d15ad78ccc888a9c7a78ef58cb61b0f1e32"),
}



# ============================================================
# Ground Station Configuration
# ============================================================
"""
Ground station 1 and 2 are configured differently. 
Defaults GS=1, the original ARGUS module.
GS=2 is an adapted station. 
"""
parser = argparse.ArgumentParser()
parser.add_argument("--gs", default=1, help="choose ground station 1 or 2 (default=1).", type=int)
args = parser.parse_args()
GS = args.gs
GS_CHANNEL = 1 if GS == 2 else 0
GS_INTERRUPT = 23 if GS == 2 else 19


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

ARGUS_FREQ = 435.0  # MHz

# ============================================================
# Satellite config
# ============================================================

SAT_CALLSIGNS = {
    1: "CT6xxx",
    2: "CT6xxx",
}
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
print(f"Ground Station No.  : {GS}")
for _sat_id, _key in SAT_AUTH_KEYS.items():
    print(f"Auth Key (SAT{_sat_id})   : {_mask_key(_key)}")

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
for _sat_id, _callsign in SAT_CALLSIGNS.items():
    print(f"  SAT{_sat_id}        : {_callsign}")

print("=" * 55 + "\n")
