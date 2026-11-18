#!/usr/bin/env python3
"""Entry program for make.fun news-image-20261118.

Validates the bundled front-page picture against the competition
limits (a whole PNG or JPEG, at most 1 MiB, at most 1024x1024) and
copies it byte for byte to entry.png in the output directory.
Standard library only; the copy is deterministic, so two runs write
identical bytes.
"""

import hashlib
import os
import struct
import sys

MAX_BYTES = 1048576
MAX_DIM = 1024


def fail(message):
    print("entry failed: " + message, file=sys.stderr)
    sys.exit(1)


def read_png_size(data):
    """Return (width, height) from a PNG header, or None."""
    if len(data) < 33 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    if data[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def read_jpeg_size(data):
    """Return (width, height) from a JPEG header, or None."""
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        return None
    pos = 2
    while pos + 9 < len(data):
        if data[pos] != 0xFF:
            return None
        marker = data[pos + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            height, width = struct.unpack(">HH", data[pos + 5:pos + 9])
            return width, height
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        seg_len = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        pos += 2 + seg_len
    return None


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, "entry.png")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    target = os.path.join(out_dir, "entry.png")

    if not os.path.isfile(source):
        fail("bundled entry.png not found next to main.py")

    with open(source, "rb") as handle:
        data = handle.read()

    if len(data) > MAX_BYTES:
        fail("image is %d bytes, over the 1 MiB limit" % len(data))

    size = read_png_size(data)
    kind = "PNG"
    if size is None:
        size = read_jpeg_size(data)
        kind = "JPEG"
    if size is None:
        fail("image is neither a whole PNG nor a whole JPEG")
    width, height = size
    if width > MAX_DIM or height > MAX_DIM:
        fail("image is %dx%d, over the 1024x1024 limit" % (width, height))

    os.makedirs(out_dir, exist_ok=True)
    with open(target, "wb") as handle:
        handle.write(data)

    digest = hashlib.sha256(data).hexdigest()
    with open(target, "rb") as handle:
        written = handle.read()
    if hashlib.sha256(written).hexdigest() != digest:
        fail("written file does not match the bundled image")
    print("wrote %s (%s, %dx%d, %d bytes, sha256 %s)"
          % (target, kind, width, height, len(data), digest))


if __name__ == "__main__":
    main()
