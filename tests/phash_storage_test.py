import tempfile
from pathlib import Path

from inline_snapshot._external._external_location import ExternalLocation

from inline_snapshot_phash import PerceptualHashStorage


def test_phash_storage_basic():
    """Test basic phash storage operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = PerceptualHashStorage(Path(tmpdir))

        # Create a minimal test image (1x1 PNG)
        test_image = Path(tmpdir) / "test.png"
        # Minimal valid PNG file (1x1 transparent pixel)
        png_data = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
            b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        test_image.write_bytes(png_data)

        location = ExternalLocation("phash", "", ".png", None, None)

        # Test new_location - should compute phash
        new_loc = storage.new_location(location, test_image)
        assert new_loc.stem  # Should have computed a hash
        assert new_loc.suffix == ".png"

        # Test store
        storage.store(new_loc, test_image)
        stored_file = Path(tmpdir) / f"{new_loc.stem}.png"
        assert stored_file.exists()

        # Test load
        with storage.load(new_loc) as loaded_path:
            assert loaded_path.exists()
            assert loaded_path.read_bytes() == png_data

        # Test delete
        storage.delete(new_loc)
        assert not stored_file.exists()


def test_phash_storage_gitignore():
    """Test that storage creates .gitignore."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = PerceptualHashStorage(Path(tmpdir))
        storage._ensure_directory()

        gitignore = Path(tmpdir) / ".gitignore"
        assert gitignore.exists()
        assert b"*" in gitignore.read_bytes()
