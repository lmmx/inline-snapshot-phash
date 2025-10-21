import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

try:
    import czkawka as cz
except ImportError:
    raise ImportError(
        "czkawka is required for phash storage. Install with: pip install czkawka"
    )

from inline_snapshot._external._external_location import ExternalLocation
from inline_snapshot._external._storage._protocol import (
    StorageLookupError,
    StorageProtocol,
)


class PerceptualHashStorage(StorageProtocol):
    """Storage protocol using perceptual hashing for content-based addressing."""

    name = "phash"

    def __init__(self, directory: Path):
        self.directory = Path(directory)
        self.finder = cz.ImageSimilarity()

    def _ensure_directory(self):
        self.directory.mkdir(exist_ok=True, parents=True)
        gitignore = self.directory / ".gitignore"
        if not gitignore.exists():
            gitignore.write_bytes(b"# Perceptual hash storage\n*\n")

    def new_location(
        self, location: ExternalLocation, file_path: Path
    ) -> ExternalLocation:
        # I don't understand why this PNG file path appears to have been hashed
        # (Pdb++) p file_path
        # PosixPath('/tmp/inline-snapshot-n1v6noil/tmp-path-bec195a3-9a6c-4a9a-bf72-7e7fa967c830')
        # For now just copy the file (cannot symlink, it gets resolved)
        tmp_with_ext = file_path.with_suffix(".png")
        shutil.copy(file_path, tmp_with_ext)
        phash = self.finder.hash_image(str(tmp_with_ext))
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

    def sync_used_externals(self, used_externals):
        raise NotImplementedError("trim not yet implemented for phash storage")
