"""
Digipeater End-to-End Test Script
----------------------------------
Sends a raw AX.25 UI frame over LoRa to the CubeSat and listens for the
digipeated response. A successful test shows the satellite callsign appended
to the via-path with the H-bit (has-been-repeated) set.

Prerequisites:
  - CubeSat must NOT be in STARTUP state
  - Digipeater must be activated: send DIGIPEATER_ACTIVATE via the normal GS
    before running this script (DigipeaterState defaults to inactive on boot)

Usage:
  python scripts/test_digipeater.py
  python scripts/test_digipeater.py --count 5 --interval 10
  python scripts/test_digipeater.py --dest CQ --payload "HELLO WORLD" --timeout 20
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
# AX.25 frame helpers
# These mirror the logic in FSW flight/apps/digipeater/ax25.py so the test
# script has no dependency on the FSW codebase.
# ---------------------------------------------------------------------------

_AX25_ADDR_LEN = 7
_AX25_CONTROL_UI = 0x03  # Unnumbered Information frame
_AX25_PID_NO_L3 = 0xF0   # No layer-3 protocol


def _encode_ax25_address(callsign, ssid=0, last=False, h_bit=False):
    """Encode a callsign into a 7-byte AX.25 address entry."""
    padded = (callsign.upper() + "      ")[:6]
    addr = bytearray(7)
    for i in range(6):
        addr[i] = ord(padded[i]) << 1
    ssid_byte = 0x60  # reserved bits (R R = 1 1)
    ssid_byte |= (ssid & 0x0F) << 1
    if h_bit:
        ssid_byte |= 0x80
    if last:
        ssid_byte |= 0x01
    addr[6] = ssid_byte
    return bytes(addr)


def build_ax25_ui_frame(dest, src, info=b"", dest_ssid=0, src_ssid=0):
    """Build a minimal AX.25 UI frame with no via-path entries.

    Structure: [Dest(7)] [Src(7)] [Control(1)] [PID(1)] [Info(variable)]
    The source address has the extension bit set (last address in field).
    """
    dest_addr = _encode_ax25_address(dest, ssid=dest_ssid, last=False, h_bit=False)
    src_addr = _encode_ax25_address(src, ssid=src_ssid, last=True, h_bit=False)
    return dest_addr + src_addr + bytes([_AX25_CONTROL_UI, _AX25_PID_NO_L3]) + info


def decode_ax25_addresses(data):
    """Parse the AX.25 address field from raw frame bytes.

    Returns:
        (addresses, addr_end) where addresses is a list of dicts:
            {callsign, ssid, h_bit, last}
        and addr_end is the byte offset where the address field ends.
        Returns (None, None) if the data is too short or malformed.
    """
    addresses = []
    i = 0
    while i + _AX25_ADDR_LEN <= len(data):
        callsign = ""
        for j in range(6):
            callsign += chr(data[i + j] >> 1)
        callsign = callsign.strip()
        ssid_byte = data[i + 6]
        ssid = (ssid_byte >> 1) & 0x0F
        h_bit = bool(ssid_byte & 0x80)
        last = bool(ssid_byte & 0x01)
        addresses.append({"callsign": callsign, "ssid": ssid, "h_bit": h_bit, "last": last})
        i += _AX25_ADDR_LEN
        if last:
            return addresses, i
    return None, None


def _print_addresses(addresses):
    """Pretty-print a decoded AX.25 address list."""
    labels = ["Dest", "Src"] + [f"Via[{k}]" for k in range(len(addresses) - 2)]
    for label, addr in zip(labels, addresses):
        ssid_str = f"-{addr['ssid']}" if addr["ssid"] else ""
        h_str = " [H]" if addr["h_bit"] else ""
        print(f"    {label:<8}: {addr['callsign']}{ssid_str}{h_str}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Send AX.25 frames to the CubeSat and verify digipeater relay."
    )
    parser.add_argument("--count", type=int, default=3, help="Number of test frames to send (default: 3)")
    parser.add_argument("--interval", type=float, default=5.0, help="Seconds between sends (default: 5.0)")
    parser.add_argument("--dest", default="APRS", help="AX.25 destination callsign (default: APRS)")
    parser.add_argument("--payload", default="DIGI TEST", help="Info field text (default: 'DIGI TEST')")
    parser.add_argument("--timeout", type=float, default=15.0, help="RX wait timeout per packet in seconds (default: 15.0)")
    args = parser.parse_args()

    print("=" * 60)
    print("  Digipeater End-to-End Test")
    print("=" * 60)
    print(f"  Radio frequency : {ARGUS_FREQ} MHz")
    print(f"  GS callsign     : {GS_CALLSIGN}  (frame source)")
    print(f"  SC callsign     : {SC_CALLSIGN}  (expected in via-path)")
    print(f"  Frame dest      : {args.dest}")
    print(f"  Test frames     : {args.count}")
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
        info = f"{args.payload} #{i + 1}".encode()
        frame = build_ax25_ui_frame(args.dest, GS_CALLSIGN, info=info)

        print(f"[TX #{i + 1}/{args.count}]")
        print(f"  Dest    : {args.dest}")
        print(f"  Src     : {GS_CALLSIGN}")
        print(f"  Info    : {info.decode()}")
        print(f"  Bytes   : {frame.hex()}")
        print(f"  Length  : {len(frame)} bytes")

        radio.send(frame)
        radio.set_mode_rx()
        radio.receive_success = False

        print(f"  Sent. Waiting up to {args.timeout}s for digipeated response...")

        deadline = time.time() + args.timeout
        got_pass = False

        while time.time() < deadline:
            if radio.receive_success:
                payload = radio.last_payload
                radio.receive_success = False

                msg = payload.message
                print(f"\n  [RX] {len(msg)} bytes  RSSI: {payload.rssi} dBm  SNR: {payload.snr} dB")
                print(f"       Raw: {msg.hex()}")

                addresses, addr_end = decode_ax25_addresses(msg)
                if addresses is None:
                    print("       Not an AX.25 frame (likely a SPLAT heartbeat from satellite)")
                    # Keep waiting — the actual digipeated frame may still arrive
                    continue

                print("       Addresses:")
                _print_addresses(addresses)

                via_entries = addresses[2:]
                sat_in_path = any(
                    a["callsign"].strip().upper() == SC_CALLSIGN.strip().upper() and a["h_bit"]
                    for a in via_entries
                )

                if sat_in_path:
                    print(f"\n  [PASS] {SC_CALLSIGN} found in via-path with H-bit set — digipeater is working!")
                    got_pass = True
                    passed += 1
                    break
                else:
                    print(f"\n  [INFO] {SC_CALLSIGN} not in via-path (likely a different packet, still waiting...)")
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
