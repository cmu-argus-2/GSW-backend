#!/usr/bin/env python3
import sys
import math
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image

DH_MAGIC = b"DHGEN"
DH_FILE_HEADER_SIZE = 5
DH_PACKET_HEADER_SIZE = 2
DH_MAX_PAYLOAD_SIZE = 240
DH_FIXED_PACKET_SIZE = DH_PACKET_HEADER_SIZE + DH_MAX_PAYLOAD_SIZE

TILEPACK_HDR_SIZE = 7  # payload_size(u16), page_id(u16), tile_idx(u16), frag_idx(u8)

DEFAULT_TARGET_W = 640
DEFAULT_TARGET_H = 480
DEFAULT_TILE_W = 64
DEFAULT_TILE_H = 32


def read_dh_packets(path: Path) -> List[bytes]:
    data = path.read_bytes()
    packets: List[bytes] = []

    if data.startswith(DH_MAGIC):
        offset = DH_FILE_HEADER_SIZE
        while offset + DH_FIXED_PACKET_SIZE <= len(data):
            block = data[offset:offset + DH_FIXED_PACKET_SIZE]
            payload_len = (block[0] << 8) | block[1]
            if payload_len == 0:
                break
            payload = block[DH_PACKET_HEADER_SIZE:DH_PACKET_HEADER_SIZE + payload_len]
            packets.append(payload)
            offset += DH_FIXED_PACKET_SIZE
    else:
        # Raw file: consecutive tilepack packets (header + payload)
        offset = 0
        while offset + TILEPACK_HDR_SIZE <= len(data):
            hdr = data[offset:offset + TILEPACK_HDR_SIZE]
            payload_len = (hdr[0] << 8) | hdr[1]
            total = TILEPACK_HDR_SIZE + payload_len
            if offset + total > len(data):
                break
            packets.append(data[offset:offset + total])
            offset += total

    return packets


def parse_tilepack_packets(payloads: List[bytes]) -> Dict[int, List[Tuple[int, bytes]]]:
    tiles: Dict[int, List[Tuple[int, bytes]]] = defaultdict(list)
    for buf in payloads:
        if len(buf) < TILEPACK_HDR_SIZE:
            continue
        payload_size = (buf[0] << 8) | buf[1]
        tile_idx = (buf[4] << 8) | buf[5]
        frag_idx = buf[6]
        payload = buf[TILEPACK_HDR_SIZE:TILEPACK_HDR_SIZE + payload_size]
        tiles[tile_idx].append((frag_idx, payload))
    return tiles


def reconstruct_tiles(tiles: Dict[int, List[Tuple[int, bytes]]]) -> Dict[int, Image.Image]:
    tile_images: Dict[int, Image.Image] = {}
    for tile_idx, frags in tiles.items():
        frags.sort(key=lambda x: x[0])
        jpeg_bytes = b"".join(part for _, part in frags)
        try:
            img = Image.open(BytesIO(jpeg_bytes)).convert("RGB")
            tile_images[tile_idx] = img
        except Exception:
            continue
    return tile_images


def stitch(tile_images: Dict[int, Image.Image], tiles_x: int, tiles_y: int, tile_w: int, tile_h: int) -> Image.Image:
    out = Image.new("RGB", (tiles_x * tile_w, tiles_y * tile_h))

    # Fill missing tiles with black
    for idx in range(tiles_x * tiles_y):
        if idx in tile_images:
            img = tile_images[idx]
        else:
            img = Image.new("RGB", (tile_w, tile_h), (0, 0, 0))

        y = idx // tiles_x
        x = idx % tiles_x
        out.paste(img, (x * tile_w, y * tile_h))

    return out


def bin_to_png(input_file: str, output_file: str):
    
    input_file = Path(input_file)
    output_file = Path(output_file)
    
    tiles_x = math.ceil(DEFAULT_TARGET_W / DEFAULT_TILE_W)
    tiles_y = math.ceil(DEFAULT_TARGET_H / DEFAULT_TILE_H)

    payloads = read_dh_packets(input_file)
    tiles = parse_tilepack_packets(payloads)
    tile_images = reconstruct_tiles(tiles)

    if not tile_images:
        raise SystemExit("No tiles reconstructed. Check input file.")

    result = stitch(tile_images, tiles_x, tiles_y, DEFAULT_TILE_W, DEFAULT_TILE_H)
    result.save(output_file)
    print(f"Saved {output_file}")
    

if __name__ == "__main__":

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])
    bin_to_png(input_file, output_file)