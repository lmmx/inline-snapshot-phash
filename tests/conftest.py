from struct import pack
from zlib import compress, crc32

import pytest


def _png_from_rows(w, h, row_generator):
    """Build PNG bytes from a row generator function."""

    def chk(t, d):
        return pack("!I", len(d)) + t + d + pack("!I", crc32(t + d) & 0xFFFFFFFF)

    raw = b"".join(b"\0" + row_generator(y) for y in range(h))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chk(b"IHDR", pack("!2I5B", w, h, 8, 2, 0, 0, 0))
        + chk(b"IDAT", compress(raw))
        + chk(b"IEND", b"")
    )


def fill_png_bytes(w=64, h=64, c=(0, 128, 255)):
    """Generate PNG image bytes with solid color fill."""
    return _png_from_rows(w, h, lambda y: bytes(c) * w)


@pytest.fixture
def red_square() -> bytes:
    """Create a red 100px square PNG image."""
    return fill_png_bytes(100, 100, (255, 0, 0))
