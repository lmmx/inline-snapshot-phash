# inline-snapshot-phash

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![pdm-managed](https://img.shields.io/badge/pdm-managed-blueviolet)](https://pdm.fming.dev)
[![PyPI](https://img.shields.io/pypi/v/inline-snapshot-phash.svg)](https://pypi.org/project/inline-snapshot-phash)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/inline-snapshot-phash.svg)](https://pypi.org/project/inline-snapshot-phash)
[![License](https://img.shields.io/pypi/l/inline-snapshot-phash.svg)](https://pypi.python.org/pypi/inline-snapshot-phash)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/lmmx/inline-snapshot-phash/master.svg)](https://results.pre-commit.ci/latest/github/lmmx/inline-snapshot-phash/master)

Perceptual hash storage protocol for inline-snapshot.

## Features

- **Perceptual hashing for content-based addressing**: Images are stored and identified by their perceptual hash rather than exact byte matching
- **Automatic deduplication**: Perceptually identical images (e.g., same content in different formats) share a single archived file
- **Fast hash comparison**: Test runs compare hash strings without loading images from disk
- **Archived files for inspection**: Original images remain available for manual visual comparison when outputs change
- **(Future) Tolerance-based comparison**: Support for near-matches within a configurable similarity threshold

## Installation

```bash
pip install inline-snapshot-phash
```

### Requirements

- Python 3.8+
- inline-snapshot >= 0.30.1
- czkawka >= 0.1.1

## Quick Start

Register the storage protocol in your `conftest.py`:

```python
from inline_snapshot_phash import register_phash_storage

register_phash_storage()  # noqa: F401
```

Then use the `phash:` protocol in your tests:

```python
from pathlib import Path
from inline_snapshot import external

def test_image_output():
    output_path = generate_diagram()  # Returns Path to a .png file
    assert output_path == external("phash:")
```

On first run with `--inline-snapshot=create`, this generates:

```python
def test_image_output():
    output_path = generate_diagram()
    assert output_path == external("phash:8LS0tOSwvLQ.png")
```

The image is archived at `.inline-snapshot/phash/8LS0tOSwvLQ.png`, and subsequent test runs compare perceptual hashes without loading the image file.

## Demo

A minimal demo test suite is provided in `demo/demo_test.py` showing the three core behaviors:

- basic phash snapshot creation
- different images producing different hashes
  - The `test_red_square` and `test_blue_square` tests produce different snapshots.
- identical images sharing archived storage (one-to-many behavior).
  - The `test_red_square` and `test_red_square_tiny` tests produce the same snapshot because the
    2px wide square PNG has the same perceptual hash as the 100px one.

Run `pytest --inline-snapshot=create demo/demo_test.py` to see it in action.

## How It Works

### Property-Based Similarity

Traditional snapshot testing assumes deterministic processes that produce byte-identical outputs. The `phash:` protocol instead snapshots based on perceptual similarity—a property of the image content rather than exact byte matching.

For example, if 10 test functions each generate a red square (as PNG, JPG, at different sizes), they all produce the same perceptual hash. One archived image file serves all 10 tests, and hash comparisons pass without redundant storage.

### Storage Flow

1. You write `assert output_path == external("phash:")`
2. inline-snapshot computes the perceptual hash of the image at `output_path`
3. The code updates to `assert output_path == external("phash:8LS0tOSwvLQ.png")`
4. The original image is stored at `.inline-snapshot/phash/8LS0tOSwvLQ.png`

On subsequent test runs:
- The perceptual hash of the new output is computed
- It's compared against `8LS0tOSwvLQ` from the snapshot string
- If they match, the test passes (no file I/O after initial hash computation)
- If different, inline-snapshot shows a diff and offers to update

### Why Both Hash and File?

The hash enables fast comparison during test runs—just string matching, no image loading. The archived file provides a reference for manual visual inspection when test outputs change.

For example, in page dewarping optimization (flattening curved book pages from photos), you want to avoid:
- Constantly reviewing tests when optimization tweaks change outputs slightly (but imperceptibly)
- Naively accepting snapshot updates without understanding what changed

The phash approach separates "did perceptual quality change?" (the test assertion) from "what exactly changed?" (manual inspection of archived images).

### One-to-Many Behavior

This protocol deliberately deduplicates perceptually similar images. When `create_image2()` changes, you diff against whichever test first generated that hash (e.g., `create_image1()`'s archive), not the last run of `create_image2()`.

This is the intended behavior: files with the same phash are treated as identical, similar to git's SHA256 content addressing but for perceptual equivalence. For more discussion on this design decision and use cases, see [inline-snapshot discussion #311](https://github.com/15r10nk/inline-snapshot/discussions/311).

## Contributing

Maintained by [lmmx](https://github.com/lmmx). Contributions welcome!

1. **Issues & Discussions**: Please open a GitHub issue for bugs or feature requests. For design discussions, see the [upstream inline-snapshot discussion #311](https://github.com/15r10nk/inline-snapshot/discussions/311).
2. **Pull Requests**: PRs are welcome!
   - Install the dev environment with [uv](https://docs.astral.sh/uv/): `uv sync`
   - Run tests with `$(uv python find) -m pytest` and include updates to docs or examples if relevant.
   - If reporting a bug, please include the version and the error message/traceback if available.

This is a third-party extension for [inline-snapshot](https://github.com/15r10nk/inline-snapshot).

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
