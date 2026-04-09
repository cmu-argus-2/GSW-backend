#!/usr/bin/env python3
"""
Reconstruct an image from a transaction .pkl file.

The .pkl contains a fragment_dict: {seq_number: bytes_payload, ...}
The companion .json contains metadata (number_of_packets, file_path, etc.)

Usage:
    python pkl_to_image.py <path_to_pkl> [output_path.png]

If output_path is omitted, saves as <pkl_name>.png next to the pkl file.
"""

import json
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.bin_to_png import bin_to_png


def pkl_to_image(pkl_path: str, output_path: str = None):
    pkl_path = Path(pkl_path)
    if not pkl_path.exists():
        raise FileNotFoundError(f"PKL file not found: {pkl_path}")

    # Load fragment dict from pkl
    with open(pkl_path, "rb") as f:
        fragment_dict = pickle.load(f)

    # Try to read number_of_packets from companion JSON
    json_path = pkl_path.with_suffix(".json")
    num_packets = None
    if json_path.exists():
        with open(json_path) as f:
            metadata = json.load(f)
        num_packets = metadata.get("number_of_packets")
        print(f"Metadata: tid={metadata.get('tid')}, "
              f"file={metadata.get('file_path')}, "
              f"packets={num_packets}, "
              f"missing={metadata.get('len_missing_fragments')}")

    if num_packets is None:
        num_packets = max(fragment_dict.keys()) + 1

    print(f"Loaded {len(fragment_dict)}/{num_packets} fragments")

    # Reassemble fragments in order into a single binary blob
    bin_path = pkl_path.with_suffix(".bin")
    with open(bin_path, "wb") as f:
        for i in range(num_packets):
            frag = fragment_dict.get(i)
            if frag is None:
                print(f"  WARNING: fragment {i} missing, writing zeros")
                # estimate size from a known fragment
                size = len(next(iter(fragment_dict.values())))
                f.write(b"\x00" * size)
            else:
                f.write(frag)

    print(f"Reassembled binary: {bin_path} ({bin_path.stat().st_size} bytes)")

    # Convert bin -> png using existing pipeline
    if output_path is None:
        output_path = str(pkl_path.with_suffix(".png"))

    bin_to_png(str(bin_path), output_path)
    print(f"Image saved: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path_to.pkl> [output.png]")
        sys.exit(1)

    pkl_file = sys.argv[1]
    out_file = sys.argv[2] if len(sys.argv) > 2 else None
    pkl_to_image(pkl_file, out_file)
