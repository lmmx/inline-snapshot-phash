import tempfile
from pathlib import Path

from inline_snapshot_phash._format import ImageFormat


def test_format_round_trip(red_square):
    """Format should satisfy: format.decode(format.encode(value)) == value"""

    with tempfile.TemporaryDirectory() as tmpdir:
        # Original value: a Path to an image
        snapshot_path = Path(tmpdir) / "snapshot.ph"
        ImageFormat.encode(red_square, snapshot_path)
        decoded_value = ImageFormat.decode(snapshot_path)
        assert red_square == decoded_value
