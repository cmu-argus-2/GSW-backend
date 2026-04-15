"""
Digipeater End-to-End Test Script
----------------------------------
Sends a LoRa APRS plain-text packet to the CubeSat and listens for the
digipeated response. A successful test shows the satellite callsign with a
trailing '*' replacing the WIDE1-1 token in the via-path.

Prerequisites:
  - CubeSat must NOT be in STARTUP state
  - Digipeater must be activated: send DIGIPEATER_ACTIVATE via the normal GS
    before running this script (DigipeaterState defaults to inactive on boot)

Usage:
  python scripts/test_digipeater.py
  python scripts/test_digipeater.py --count 5 --interval 10
  python scripts/test_digipeater.py --payload "HELLO WORLD" --timeout 20
"""

import argparse
import os
import sys
import time

# Allow imports from the repo root (lib/) when running as a script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.config import ARGUS_FREQ, GS_CALLSIGN, SC_CALLSIGN
from lib.radio_utils import initialize_radio

# ---------------------------------------------------------------------------
# LoRa APRS packet helpers
# ---------------------------------------------------------------------------

_LORA_APRS_HEADER = b"\x3c\xff\x01"
_APRS_TOCALL = "APLRT1"
_APRS_PATH = "WIDE1-1"


def build_lora_aprs_packet(src, payload, tocall=_APRS_TOCALL, path=_APRS_PATH):
    """Build a LoRa APRS plain-text packet.

    Wire format: [0x3C][0xFF][0x01]SRC>TOCALL,PATH:payload
    """
    aprs_str = f"{src}>{tocall},{path}:{payload}"
    return _LORA_APRS_HEADER + aprs_str.encode("ascii")


def parse_lora_aprs_packet(data):
    """Parse a raw LoRa APRS packet into its components.

    Returns a dict with keys: src, tocall, path_tokens, payload
    Returns None if the packet is not a valid LoRa APRS packet.
    """
    if not data or len(data) < len(_LORA_APRS_HEADER) + 1:
        return None
    if data[: len(_LORA_APRS_HEADER)] != _LORA_APRS_HEADER:
        return None
    try:
        aprs_str = data[len(_LORA_APRS_HEADER) :].decode("ascii")
    except (UnicodeDecodeError, ValueError):
        return None

    gt_idx = aprs_str.find(">")
    if gt_idx < 1:
        return None
    colon_idx = aprs_str.find(":", gt_idx + 1)
    if colon_idx < 0:
        return None

    src = aprs_str[:gt_idx]
    tocall_and_path = aprs_str[gt_idx + 1 : colon_idx]
    payload = aprs_str[colon_idx + 1 :]

    parts = tocall_and_path.split(",")
    tocall = parts[0]
    path_tokens = parts[1:]

    return {"src": src, "tocall": tocall, "path_tokens": path_tokens, "payload": payload}


def _print_aprs_packet(parsed):
    """Pretty-print a parsed LoRa APRS packet."""
    print(f"    Src     : {parsed['src']}")
    print(f"    Tocall  : {parsed['tocall']}")
    print(f"    Path    : {','.join(parsed['path_tokens']) if parsed['path_tokens'] else '(none)'}")
    print(f"    Payload : {parsed['payload']}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Send LoRa APRS packets to the CubeSat and verify digipeater relay."
    )
    parser.add_argument("--count", type=int, default=3, help="Number of test packets to send (default: 3)")
    parser.add_argument("--interval", type=float, default=5.0, help="Seconds between sends (default: 5.0)")
    parser.add_argument("--payload", default="DIGI TEST", help="APRS info field text (default: 'DIGI TEST')")
    parser.add_argument("--timeout", type=float, default=15.0, help="RX wait timeout per packet in seconds (default: 15.0)")
    args = parser.parse_args()

    print("=" * 60)
    print("  Digipeater End-to-End Test")
    print("=" * 60)
    print(f"  Radio frequency : {ARGUS_FREQ} MHz")
    print(f"  GS callsign     : {GS_CALLSIGN}  (packet source)")
    print(f"  SC callsign     : {SC_CALLSIGN}  (expected in via-path with *)")
    print(f"  APRS path       : {_APRS_PATH}")
    print(f"  Test packets    : {args.count}")
    print(f"  Send interval   : {args.interval}s")
    print(f"  RX timeout      : {args.timeout}s")
    print()
    print("[NOTE] The digipeater must be activated on the CubeSat before")
    print("       running this test. Send DIGIPEATER_ACTIVATE via the normal")
    print("       ground station software first.")
    print("=" * 60)
    print()

    print("Initializing radio...")
    radio = initialize_radio()
    radio.set_mode_rx()
    radio.receive_success = False
    print("Radio ready.\n")

    passed = 0
    failed = 0

    for i in range(args.count):
        payload_str = f"{args.payload} #{i + 1}"
        packet = build_lora_aprs_packet(GS_CALLSIGN, payload_str)

        print(f"[TX #{i + 1}/{args.count}]")
        print(f"  Src     : {GS_CALLSIGN}")
        print(f"  Path    : {_APRS_PATH}")
        print(f"  Payload : {payload_str}")
        print(f"  Bytes   : {packet.hex()}")
        print(f"  Length  : {len(packet)} bytes")

        radio.send(packet)
        radio.set_mode_rx()
        radio.receive_success = False

        print(f"  Sent. Waiting up to {args.timeout}s for digipeated response...")

        deadline = time.time() + args.timeout
        got_pass = False

        while time.time() < deadline:
            if radio.receive_success:
                raw = radio.last_payload
                radio.receive_success = False

                msg = raw.message
                print(f"\n  [RX] {len(msg)} bytes  RSSI: {raw.rssi} dBm  SNR: {raw.snr} dB")
                print(f"       Raw: {msg.hex()}")

                parsed = parse_lora_aprs_packet(msg)
                if parsed is None:
                    print("       Not a LoRa APRS packet (likely a SPLAT heartbeat from satellite)")
                    # Keep waiting — the actual digipeated frame may still arrive
                    continue

                print("       Parsed:")
                _print_aprs_packet(parsed)

                expected_token = SC_CALLSIGN.strip().upper() + "*"
                sat_in_path = any(
                    t.strip().upper() == expected_token for t in parsed["path_tokens"]
                )

                if sat_in_path:
                    print(f"\n  [PASS] {expected_token} found in via-path — digipeater is working!")
                    got_pass = True
                    passed += 1
                    break
                else:
                    print(f"\n  [INFO] {expected_token} not in via-path (likely a different packet, still waiting...)")
                    # Keep waiting

            time.sleep(0.05)

        if not got_pass:
            print(f"\n  [FAIL] No digipeated frame received within {args.timeout}s")
            failed += 1

        print()
        if i < args.count - 1:
            time.sleep(args.interval)

    print("=" * 60)
    print(f"  Results: {passed}/{args.count} passed, {failed}/{args.count} failed")
    print("=" * 60)

    radio.close()
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
