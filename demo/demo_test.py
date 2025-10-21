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


def fill_png_bytes(w=64, h=64, c=(0, 128, 255)):
    """Generate PNG image bytes with given width, height, and RGB color."""

    def chk(t, d):
        return pack("!I", len(d)) + t + d + pack("!I", crc32(t + d) & 0xFFFFFFFF)

    raw = b"".join(b"\0" + bytes(c) * w for _ in range(h))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chk(b"IHDR", pack("!2I5B", w, h, 8, 2, 0, 0, 0))
        + chk(b"IDAT", compress(raw))
        + chk(b"IEND", b"")
    )


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
def blue_square(tmp_path: Path) -> Path:
    """Create a blue 100px square PNG image."""
    img_path = tmp_path / "blue_square.png"
    img_path.write_bytes(fill_png_bytes(100, 100, (0, 0, 255)))
    return img_path


def test_red_square(red_square: Path):
    """Basic usage: 100px red square gets a phash."""
    assert red_square == external("phash:AAAAAAAAAAA")


def test_blue_square(blue_square: Path):
    """Different image gets different phash."""
    assert blue_square == external("phash:")


def test_red_square_again(red_square: Path):
    """Same image at different resolution shares the same phash (one-to-many behavior).

    Note: either this test will save its output or the `test_red_square` snapshot will,
    not both! Since the hash matches, they get deduplicated and only saved to disk once.
    """
    assert red_square_tiny == external("phash:")  # matches `test_red_square` snapshot
