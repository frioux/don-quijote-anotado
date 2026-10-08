#!/usr/bin/env python3
"""Print Ormsby's chapter from the Standard Ebooks source as plain text,
one paragraph per block, with his note references inline as [note-NNN],
followed by the text of each of those notes.

usage: ormsby_text.py PART CHAPTER
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def strip(s: str) -> str:
    s = re.sub(r"<a [^>]*href=\"endnotes\.xhtml#(note-\d+)\"[^>]*>\d+</a>", r" [\1]", s)
    s = re.sub(r"<br\s*/?>", " / ", s)
    s = re.sub(r"</span>\s*<span[^>]*>", " / ", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s).replace("\u2060", "")
    return re.sub(r"\s+", " ", s).strip()


def main(part, chapter):
    src = (ROOT / f"sources/se-chapter-{part}-{chapter}.xhtml").read_text(encoding="utf-8")
    body = src.split("<body", 1)[1]
    blocks = re.findall(r"<(p|blockquote|h3)\b[^>]*>(.*?)</\1>", body, re.S)
    notes = []
    for tag, inner in blocks:
        if tag == "blockquote":
            # a poem: one line per <p>, keep them as separate lines
            for pm in re.findall(r"<p[^>]*>(.*?)</p>", inner, re.S):
                print("    " + strip(pm))
            print()
            notes += re.findall(r"note-\d+", inner)
            continue
        t = strip(inner)
        if t:
            print(t)
            print()
        notes += re.findall(r"note-\d+", inner)
    seen = []
    for n in notes:
        if n not in seen:
            seen.append(n)
    if seen:
        end = (ROOT / "sources/se-endnotes.xhtml").read_text(encoding="utf-8")
        print("---- Ormsby's notes ----")
        for n in seen:
            m = re.search(rf'<li id="{n}"[^>]*>(.*?)</li>', end, re.S)
            txt = strip(m.group(1)) if m else "(not found)"
            txt = re.sub(r"\s*↩\s*$", "", txt)
            print(f"[{n}] {txt}\n")


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
