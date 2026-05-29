#!/usr/bin/env python3
"""Generate /llms.txt from the YAML front matter of each publications/*/index.qmd.

Follows the llms.txt convention (https://llmstxt.org/): an H1 title, a blockquote
summary, then ## sections of `[title](url): notes` links. Per-paper links point at
the Markdown full text (url-md) so an LLM can read the manuscript directly.

Re-run this whenever a publication is added/updated:
    python scripts/gen-llms-txt.py
"""
import sys
from pathlib import Path

import yaml

SITE_URL = "https://quentinandre.net"
ROOT = Path(__file__).resolve().parent.parent
PUB_DIR = ROOT / "publications"


def front_matter(qmd: Path) -> dict:
    text = qmd.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    return yaml.safe_load(text[3:end]) or {}


def year(meta: dict) -> str:
    d = str(meta.get("date", ""))
    return d[:4] if d[:4].isdigit() else d


def main() -> int:
    pubs = []
    for d in sorted(PUB_DIR.iterdir()):
        qmd = d / "index.qmd"
        if not qmd.is_file():
            continue
        meta = front_matter(qmd)
        if not meta.get("publication") or not meta.get("url-md"):
            continue  # skip the listing page and any paper without a markdown version
        pubs.append((d.name, meta))

    # newest first, matching the site's publication listing
    pubs.sort(key=lambda p: str(p[1].get("date", "")), reverse=True)

    lines = [
        "# Quentin André — Research",
        "",
        "> Full-text Markdown versions of Quentin André's peer-reviewed publications "
        "in consumer behavior, judgment and decision making, and behavioral marketing. "
        "Each link below is the plain-text manuscript, intended for machine reading. "
        f"Author homepage: {SITE_URL}",
        "",
        "## Publications",
        "",
    ]

    for slug, meta in pubs:
        title = " ".join(str(meta["title"]).split())
        yr = year(meta)
        url = f"{SITE_URL}/publications/{slug}/{meta['url-md']}"
        venue = meta.get("publication", "")
        desc = " ".join(str(meta.get("description") or meta.get("abstract") or "").split())
        if len(desc) > 320:
            desc = desc[:317].rstrip() + "…"
        note_bits = [b for b in (venue, desc) if b]
        note = ". ".join(note_bits)
        doi = meta.get("doi")
        if doi:
            note += f" DOI: {doi}."
        label = f"{title} ({yr})" if yr else title
        lines.append(f"- [{label}]({url}): {note}")

    out = ROOT / "llms.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out} ({len(pubs)} publications)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
