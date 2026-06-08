"""Replace the spotlight block delimited by HTML markers in a markdown file."""
from __future__ import annotations

from pathlib import Path

START = "<!-- REVIEWER_SPOTLIGHT_START -->"
END = "<!-- REVIEWER_SPOTLIGHT_END -->"


def update_block(path: str | Path, spotlight: str) -> None:
    p = Path(path)
    content = p.read_text(encoding="utf-8")
    if START not in content or END not in content:
        raise RuntimeError(f"Markers {START}/{END} not found in {p}")
    before, _, rest = content.partition(START)
    _, _, after = rest.partition(END)
    p.write_text(f"{before}{START}\n{spotlight}\n{END}{after}", encoding="utf-8")
