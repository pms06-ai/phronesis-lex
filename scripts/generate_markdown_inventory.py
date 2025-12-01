"""
Generate a CSV inventory of every Markdown file in the repo.
Filters out vendor/runtime folders so the list focuses on project artifacts.
"""

from __future__ import annotations

import csv
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIR_NAMES = {
    ".git",
    "node_modules",
    "venv",
    "venv311",
    "__pycache__",
}
OUTPUT = ROOT / "markdown_inventory.csv"


def iter_markdown_files(base: Path) -> Iterable[Path]:
    """Yield Markdown files ignoring excluded directories."""
    for path in base.rglob("*.md"):
        if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
            continue
        yield path


def sha256(path: Path) -> str:
    """Compute file hash."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    rows = []
    for file_path in iter_markdown_files(ROOT):
        rel_path = file_path.relative_to(ROOT).as_posix()
        stat = file_path.stat()
        rows.append(
            {
                "Path": rel_path,
                "SizeKB": round(stat.st_size / 1024, 1),
                "LastWrite": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "Hash": sha256(file_path),
            }
        )

    rows.sort(key=lambda row: row["Path"].lower())

    with OUTPUT.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=["Path", "SizeKB", "LastWrite", "Hash"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"Wrote {len(rows)} entries to {OUTPUT}")


if __name__ == "__main__":
    main()


