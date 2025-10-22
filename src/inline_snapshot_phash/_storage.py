import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Iterator

try:
    import czkawka as cz
except ImportError:
    raise ImportError(
        "czkawka is required for phash storage. Install with: pip install czkawka"
    )

from inline_snapshot._change import ChangeBase, ExternalRemove
from inline_snapshot._external._external_location import ExternalLocation
from inline_snapshot._external._storage._protocol import (
    StorageLookupError,
    StorageProtocol,
)
from inline_snapshot._global_state import state


class PerceptualHashStorage(StorageProtocol):
    """Storage protocol using perceptual hashing for content-based addressing."""

    name = "phash"

    def __init__(self, directory: Path):
        self.directory = Path(directory)
        self.finder = cz.ImageSimilarity()

    def compare(self, location: ExternalLocation, other_value) -> bool:
        """Compare by computing phash of other_value and checking against stored hash."""
        # Get the stored hash from the location stem
        stored_hash = location.stem

        # Handle bytes (from the format)
        if isinstance(other_value, bytes):
            # Write bytes to a temp file so we can hash it
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(other_value)
                tmp_path = Path(tmp.name)

            try:
                new_hash = self.finder.hash_image(tmp_path)
            finally:
                tmp_path.unlink()

        elif isinstance(other_value, Path):
            # Direct path - can hash directly (not used any more)
            new_hash = self.finder.hash_image(other_value)

        else:
            return False

        # Direct string comparison since hashes should match exactly
        return stored_hash == new_hash

    def _ensure_directory(self):
        self.directory.mkdir(exist_ok=True, parents=True)
        gitignore = self.directory / ".gitignore"
        if not gitignore.exists():
            gitignore.write_bytes(b"# Perceptual hash storage\n*\n")

    def new_location(
        self, location: ExternalLocation, file_path: Path
    ) -> ExternalLocation:
        # file_path is a temp file containing the bytes
        if file_path.suffix and file_path.suffix != ".ph":
            phash = self.finder.hash_image(file_path)
        else:
            tmp_with_ext = file_path.with_suffix(".png")
            shutil.copy(file_path, tmp_with_ext)
            phash = self.finder.hash_image(tmp_with_ext)
        return location.with_stem(phash)

    def store(self, location: ExternalLocation, file_path: Path):
        self._ensure_directory()
        dest = self.directory / f"{location.stem}{location.suffix}"
        if not dest.exists():
            shutil.copy(file_path, dest)

    @contextmanager
    def load(self, location: ExternalLocation) -> Generator[Path, None, None]:
        path = self.directory / location.path
        if not path.exists():
            raise StorageLookupError(
                f"phash {location.path!r} not found in {self.directory}"
            )
        yield path

    def delete(self, location: ExternalLocation):
        path = self.directory / location.path
        if path.exists():
            path.unlink()

    def sync_used_externals(
        self, used_externals: list[ExternalLocation]
    ) -> Iterator[ChangeBase]:
        """Find and yield removal actions for unused phash snapshots."""
        # Get all files currently in phash storage
        if not self.directory.exists():
            return

        all_stored = {
            f.name
            for f in self.directory.iterdir()
            if f.is_file() and f.suffix in (".png", ".jpg", ".jpeg")
        }

        # Extract just the filenames from used externals
        used_names = {location.path for location in used_externals if location.path}

        # Find unused files (files in storage not referenced in code)
        unused = all_stored - used_names

        # Yield removal changes if trim flag is set
        if state().update_flags.trim:
            for name in unused:
                yield ExternalRemove(
                    "trim", ExternalLocation.from_name(f"phash:{name}")
                )
