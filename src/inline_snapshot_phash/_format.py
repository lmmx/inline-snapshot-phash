# src/inline_snapshot_phash/_format.py
from __future__ import annotations

from pathlib import Path

from inline_snapshot import BinaryDiff, Format, register_format


@register_format
class ImageFormat(BinaryDiff, Format[bytes]):
    """Format handler for pathlib.Path objects."""

    # File extension may vary (e.g., .png, .txt), but pHash doesn't care
    suffix = ".ph"
    priority = 10

    @staticmethod
    def is_format_for(data: object) -> bool:
        """Match bytes."""
        return isinstance(data, bytes)

    @staticmethod
    def encode(value: bytes, path: Path):
        """Copy file contents into the snapshot file."""
        path.write_bytes(value)

    @staticmethod
    def decode(path: Path) -> Path:
        """Return the external snapshot file content bytes."""
        return path.read_bytes()
