# inline-snapshot-phash

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![pdm-managed](https://img.shields.io/badge/pdm-managed-blueviolet)](https://pdm.fming.dev)
[![PyPI](https://img.shields.io/pypi/v/inline-snapshot-phash.svg)](https://pypi.org/project/inline-snapshot-phash)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/inline-snapshot-phash.svg)](https://pypi.org/project/inline-snapshot-phash)
[![License](https://img.shields.io/pypi/l/inline-snapshot-phash.svg)](https://pypi.python.org/pypi/inline-snapshot-phash)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/lmmx/inline-snapshot-phash/master.svg)](https://results.pre-commit.ci/latest/github/lmmx/inline-snapshot-phash/master)

Perceptual hash storage protocol for inline-snapshot.

## Features

- **Perceptual hashing for perceptual content-based addressing**: Images are stored and identified by their perceptual hash rather than exact byte matching
- **Automatic deduplication**: Perceptually identical images (e.g., same content in different formats or at different sizes) share a single archived file
- **Fast hash comparison**: Test runs compare hash strings without loading images from disk
- **Archived files for inspection**: Original images remain available for manual visual comparison when outputs change

## Future Plans

- **Tolerance-based comparison**: Support for near-matches within a configurable similarity threshold
- **Store metadata as context**: The real source filename that was stored could be kept as metadata
  in addition to the archived file

## Installation

```bash
uv pip install inline-snapshot-phash
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

- !!! **WIP**: non-functioning / proof of concept creation in progress !!!

A minimal demo test suite is provided in `demo/demo_test.py` showing the three core behaviors:

- basic phash snapshot creation
- different images producing different hashes
  - The `test_red_square` and `test_blue_square` tests produce different snapshots.
- identical images sharing archived storage (one-to-many behavior).
  - The `test_red_square` and `test_red_square_tiny` tests produce the same snapshot because the
    2px wide square PNG has the same perceptual hash as the 100px one.

Run `pytest --inline-snapshot=create demo/demo_test.py` to see it in action.

## How It Works

### Visual Property-Based Similarity

Traditional snapshot testing assumes deterministic processes that produce byte-identical outputs.

The `phash:` storage protocol instead snapshots based on perceptual similarity, a property of the image content rather than exact byte matching.

For example, if 10 test functions each generate a red square in different ways (as PNG, JPG, at different sizes, etc.), they all produce the same perceptual hash.
One archived image file serves all 10 tests, and perceptual hash comparisons will pass without saving redundant copies of this shared image.

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

The hash enables fast comparison during test runs: just string matching, skipping the need for image loading for test fixtures.

The archived file provides a reference for manual visual inspection when test outputs change, but
deduplication means there should not be multiple copies of the same image if you have similar tests.
This means you should be able to get the best of both worlds in more situations.

In particular where you want to avoid mass review of snapshot changes when
minor changes to the process that produced them change your outputs slightly (but imperceptibly),
which can lead to naively accepting snapshot updates without understanding what changed.

The phash approach separates whether there was a perceptual change from there being any change to the file at all.

### One-to-Many Behavior

This protocol deliberately deduplicates perceptually similar images.

This is the intended behavior: files with the same phash are treated as identical, unlike git's SHA256 content addressing which will treat any change to the file as different,
we treat only perceptual difference (as considered by the underlying pHash algorithm).

Consider you have this code:

```python
def test_1():
   assert create_image1() == external("phash:1238abe.png")

def test_2():
   assert create_image2() == external("phash:1238abe.png")
```

- Both `create_image` functions return similar images but not the exact same (they make the same phash)
- The result of `create_image2` is never saved because it is similar to `create_image1`
- You would not spot a file diff (e.g. in git) when the result of `create_image2` changes (e.g. it's the same image but enlarged 10x).
- You only see anything change when there is **perceptual** difference.
- When `create_image2()` changes, you diff against whichever test first generated that hash (e.g., `create_image1()`'s archive), not the last run of `create_image2()`.

For more discussion on this design decision and use cases, see [inline-snapshot discussion #311](https://github.com/15r10nk/inline-snapshot/discussions/311).

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
