"""Allocate a fresh result directory without changing simulation randomness."""

from pathlib import Path


def allocate_run_directory(root: str | Path = "outputs") -> Path:
    """Claim the first unused run-NNNN directory, preserving all existing runs.

    Call once for each run or export, then write stable filenames inside the
    returned directory. A failed run keeps its allocated directory for inspection.
    """
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    number = 1
    while True:
        destination = root / f"run-{number:04d}"
        try:
            destination.mkdir()
        except FileExistsError:
            number += 1
        else:
            return destination
