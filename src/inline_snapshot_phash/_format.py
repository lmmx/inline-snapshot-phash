# src/inline_snapshot_phash/_format.py
from __future__ import annotations

from pathlib import Path

from inline_snapshot import Format, TextDiff, register_format


@register_format
class PathFormat(TextDiff, Format[Path]):
    """Format handler for pathlib.Path objects."""

    # Since the suffix may vary (e.g., .png, .txt), we don’t fix it globally.
    suffix = ""  # allow dynamic suffixes

    @staticmethod
    def is_format_for(data: object) -> bool:
        """Match Path or str that points to an existing file."""
        return isinstance(data, Path)

    @staticmethod
    def encode(value: Path, path: Path):
        """Copy file contents into the snapshot file."""
        if not value.exists():
            raise FileNotFoundError(f"Cannot snapshot missing file: {value}")
        data = value.read_bytes()
        path.write_bytes(data)

    @staticmethod
    def decode(path: Path) -> Path:
        """Return the Path to the external snapshot file."""
        return path

    def rich_show(self, path: Path) -> str:
        """Render a simple description in snapshot diffs."""
        return f"[bold]{path.name}[/] ({path.stat().st_size} bytes)"

    def rich_diff(self, original: Path, new: Path) -> str:
        """Compare paths by size and modification time."""
        o = original.stat()
        n = new.stat()
        changes = []
        if o.st_size != n.st_size:
            changes.append(f"size: {o.st_size} → {n.st_size}")
        if int(o.st_mtime) != int(n.st_mtime):
            changes.append("modified time differs")
        return ", ".join(changes) or "files appear identical"
