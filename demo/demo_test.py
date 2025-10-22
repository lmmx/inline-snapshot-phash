"""Demo for inline-snapshot-phash in the form of a pytest test suite.

These tests demonstrate the perceptual hash storage protocol in action.
Run with: pytest --inline-snapshot=create demo/demo_test.py

Test logic: Three tests total - one basic usage, one showing different images get
different hashes, and one showing the same image at different sizes has the same
perceptual hash and thus is only saved once to an archived file (deduplicated).
"""

from pathlib import Path
from struct import pack
from zlib import compress, crc32

import pytest
from inline_snapshot import external

# --------- CONFTEST
from inline_snapshot_phash import register_phash_storage

register_phash_storage()  # noqa: F401

# ---------- CONFTEST


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


def checkerboard_png_bytes(w=64, h=64, cell_size=8, c1=(0, 0, 0), c2=(255, 255, 255)):
    """Generate PNG image bytes with checkerboard pattern."""

    def row(y):
        checker_y = y // cell_size
        pixels = []
        for x in range(w):
            checker_x = x // cell_size
            color = c1 if (checker_x + checker_y) % 2 == 0 else c2
            pixels.extend(color)
        return bytes(pixels)

    return _png_from_rows(w, h, row)


@pytest.fixture
def red_square(tmp_path: Path) -> Path:
    """Create a red 100px square PNG image."""
    img_path = tmp_path / "red_square.png"
    img_path.write_bytes(fill_png_bytes(100, 100, (255, 0, 0)))
    return img_path


@pytest.fixture
def red_square_tiny(tmp_path: Path) -> Path:
    """Create a red 2px square PNG image."""
    img_path = tmp_path / "red_square.png"
    img_path.write_bytes(fill_png_bytes(2, 2, (255, 0, 0)))
    return img_path


@pytest.fixture
def checkerboard(tmp_path: Path) -> Path:
    """Create a 64x64 checkerboard with 8px cells (different pattern)."""
    img_path = tmp_path / "checkerboard.png"
    img_path.write_bytes(checkerboard_png_bytes(64, 64, cell_size=8))
    return img_path


def test_red_square_one(red_square: Path):
    """Basic usage: 100px red square gets a phash."""
    assert red_square.read_bytes() == external("phash:")


def test_red_square_two(red_square_tiny: Path):
    """Same image at different resolution shares the same phash (one-to-many behavior).

    Note: either this test will save its output or the `test_red_square` snapshot will,
    not both! Since the hash matches, they get deduplicated and only saved to disk once.
    """
    # matches `test_red_square_one` snapshot
    assert red_square_tiny.read_bytes() == external("phash:")


def test_checkerboard(checkerboard: Path):
    """Different image pattern gets different phash."""
    assert checkerboard.read_bytes() == external("phash:")
