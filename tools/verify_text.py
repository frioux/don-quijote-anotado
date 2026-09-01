#!/usr/bin/env python3
"""Confirm the Spanish text in an annotated chapter YAML still matches
Project Gutenberg #2000 verbatim (modulo whitespace and quote glyphs)."""
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_chapter import spanish_chapter  # noqa: E402


def norm(s: str) -> str:
    s = s.replace("''", "").replace("«", "").replace("»", "")
    s = s.replace("“", "").replace("”", "").replace("‘", "").replace("’", "'")
    s = s.replace("— ", "—").replace("—", "— ")
    return re.sub(r"\s+", " ", s).strip()


def main(path):
    doc = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    title, src_paras = spanish_chapter(doc["part"], doc["chapter"])
    ok = norm(doc["title_es"]) == norm(title)
    if not ok:
        print("TITLE MISMATCH\n  yaml: %s\n  src:  %s" % (doc["title_es"], title))
    got = [" ".join(s["es"] for s in p["sentences"]) for p in doc["paragraphs"]]
    if len(got) != len(src_paras):
        print(f"PARAGRAPH COUNT: yaml {len(got)} vs source {len(src_paras)}")
        ok = False
    for i, (g, s) in enumerate(zip(got, src_paras), 1):
        if norm(g) != norm(s):
            ok = False
            print(f"PARAGRAPH {i} DIFFERS")
            a, b = norm(g), norm(s)
            j = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
            print("  yaml: ..." + a[max(0, j-40):j+60])
            print("  src:  ..." + b[max(0, j-40):j+60])
    n = sum(len(p["sentences"]) for p in doc["paragraphs"])
    empty = [k for k in ("literal", "ormsby") for p in doc["paragraphs"] for s in p["sentences"] if not s.get(k)]
    if empty:
        print(f"WARNING: {len(empty)} sentence fields still empty")
    print(("OK" if ok else "FAIL") + f": {len(got)} paragraphs, {n} sentence units")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(sys.argv[1])
