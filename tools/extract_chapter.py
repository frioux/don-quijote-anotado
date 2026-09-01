#!/usr/bin/env python3
"""Slice one chapter of Don Quijote out of the Gutenberg sources and emit a
skeleton YAML for annotation.

Only the Spanish `es` fields are meant to be trusted output. The Ormsby text is
dumped as a comment block at the end for hand alignment.
"""
import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
         "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX"]

SPLIT_WORDS = 50  # sentences longer than this get split at ; or :


def spanish_chapter(part: int, chapter: int):
    text = (ROOT / "sources/pg2000.txt").read_text(encoding="utf-8")
    lines = text.split("\n")
    # Part headers in PG #2000 (the 1615 book is "Segunda parte ... caballero").
    part_re = {1: r"^Primera parte del ingenioso hidalgo",
               2: r"^Segunda parte del ingenioso caballero"}[part]
    starts = [i for i, l in enumerate(lines) if re.match(part_re, l)]
    # The 1615 header appears twice (TOC + body); take the last occurrence.
    pstart = starts[-1]
    heading_re = (r"^Capítulo primero\." if chapter == 1
                  else rf"^Capítulo {ROMAN[chapter]}\.")
    cstart = next(i for i in range(pstart, len(lines)) if re.match(heading_re, lines[i], re.I))
    next_re = r"^Capítulo [IVXLC]+\.|^(Primera|Segunda|Tercera|Cuarta) parte del"
    cend = next(i for i in range(cstart + 1, len(lines)) if re.match(next_re, lines[i]))
    block = lines[cstart:cend]
    # Heading may wrap to a second line.
    head = [block[0]]
    i = 1
    while block[i].strip():
        head.append(block[i]); i += 1
    title = " ".join(h.strip() for h in head)
    paras, cur = [], []
    for l in block[i:]:
        if l.strip():
            cur.append(l.strip())
        elif cur:
            paras.append(" ".join(cur)); cur = []
    if cur:
        paras.append(" ".join(cur))
    return title, paras


def ormsby_chapter(part: int, chapter: int):
    text = (ROOT / "sources/pg996.txt").read_text(encoding="utf-8")
    lines = text.split("\n")
    heading = f"CHAPTER {ROMAN[chapter]}."
    hits = [i for i, l in enumerate(lines) if l.strip() == heading]
    # First hit is Part I body (the TOC entries lack the trailing period).
    cstart = hits[part - 1]
    cend = next(i for i in range(cstart + 1, len(lines))
                if re.match(r"^CHAPTER [IVXLC]+\.$", lines[i].strip()) or lines[i].startswith("VOLUME"))
    paras, cur = [], []
    for l in lines[cstart + 1:cend]:
        if l.strip():
            cur.append(l.strip())
        elif cur:
            paras.append(" ".join(cur)); cur = []
    if cur:
        paras.append(" ".join(cur))
    return paras


def split_sentences(para: str):
    # Split after . ! ? followed by space and an opening char. Keep the
    # terminator with the sentence. Ellipses and abbreviations are rare here.
    parts = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡«\"'—\-])", para)
    out = []
    for s in parts:
        words = len(s.split())
        if words > SPLIT_WORDS:
            chunks = re.split(r"(?<=[;:])\s+", s)
            # Re-merge tiny trailing chunks so no unit is absurdly short.
            merged = []
            for c in chunks:
                if merged and len(c.split()) < 6:
                    merged[-1] += " " + c
                else:
                    merged.append(c)
            out.extend(merged)
        else:
            out.append(s)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", type=int, required=True)
    ap.add_argument("--chapter", type=int, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    title, paras = spanish_chapter(a.part, a.chapter)
    doc = {
        "part": a.part,
        "chapter": a.chapter,
        "title_es": title,
        "title_en": "",
        "paragraphs": [],
        "summary": "",
        "context": "",
    }
    n = 0
    for p in paras:
        sents = []
        for s in split_sentences(p):
            n += 1
            sents.append({"es": s, "literal": "", "ormsby": "", "vocab": []})
        doc["paragraphs"].append({"sentences": sents})
    out = Path(a.out)
    with out.open("w", encoding="utf-8") as f:
        yaml.safe_dump(doc, f, allow_unicode=True, sort_keys=False, width=1000)
        f.write("\n# ---- Ormsby (for alignment) ----\n")
        for p in ormsby_chapter(a.part, a.chapter):
            f.write("# " + p + "\n#\n")
    print(f"{len(paras)} paragraphs, {n} sentence units -> {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
