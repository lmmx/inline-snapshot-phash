from pathlib import Path

from inline_snapshot._global_state import state

from . import _format  # noqa: F401 (auto-register Path format)
from ._storage import PerceptualHashStorage

__all__ = ["register_phash_storage", "PerceptualHashStorage", "__version__"]

__version__ = "0.1.0"


def register_phash_storage(storage_dir: Path | None = None):
    """Register the phash storage protocol with inline-snapshot.

    Users call this in their conftest.py or at the top of their test file.

    Args:
        storage_dir: Directory to store phash snapshots.
                    Defaults to .inline-snapshot/phash
    """
    if storage_dir is None:
        storage_dir = Path(".inline-snapshot") / "phash"

    state().all_storages["phash"] = PerceptualHashStorage(storage_dir)
