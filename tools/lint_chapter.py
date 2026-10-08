#!/usr/bin/env python3
"""Check an annotated chapter YAML against the rules in ANNOTATING.md.

usage: lint_chapter.py content/part1/ch12.yaml

Exit status 1 if anything is wrong. Warnings (prefixed WARN) do not fail.
"""
import re
import sys
from pathlib import Path

import yaml

FORBIDDEN = [
    (r"\bsee (the )?(note|notes?) \d", "cross-reference to another note"),
    (r"\b(as|like) in note \d", "cross-reference to another note"),
    (r"\bnotes? \d+ (and|or) \d+", "cross-reference to another note"),
    (r"\b[123](st|nd|rd) (sg|pl|sing|plur|person)\b", "grammatical person as '3rd sg.'; use a plain pronoun"),
    (r"\b[123](sg|pl)\b", "grammatical person as '3sg'; use a plain pronoun"),
]
# Ormsby's em-dashes become commas or parentheses when his note is copied in.
ORMSBY_NOTE_FORBIDDEN = [("—", "em-dash inside ormsby_note (turn it into a comma or parentheses)")]


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def walk(nodes, es, prev_es, errs, where):
    for node in nodes:
        if not isinstance(node, dict) or "s" not in node or "r" not in node:
            errs.append(f"{where}: diagram node is not {{s, r}}: {node!r}")
            continue
        s = norm(node["s"])
        # "a ... b" is allowed when both halves are in the sentence, in order.
        parts = [p.strip() for p in s.split("...") if p.strip()]
        hay = norm(es)
        pos = 0
        ok = True
        for p in parts:
            i = hay.find(p, pos)
            if i < 0:
                ok = False
                break
            pos = i + len(p)
        if not ok and prev_es:
            ok = all(norm(p) in norm(prev_es) for p in parts)
        if not ok:
            errs.append(f"{where}: diagram chunk not in sentence: {node['s']!r}")
        walk(node.get("under", []), es, prev_es, errs, where)


def main(path):
    text = Path(path).read_text(encoding="utf-8")
    doc = yaml.safe_load(text)
    errs, warns = [], []
    for k in ("part", "chapter", "title_es", "title_en", "paragraphs", "summary", "context"):
        if not doc.get(k):
            errs.append(f"missing or empty top-level field: {k}")
    if "# ---- Ormsby (for alignment) ----" in text:
        errs.append("the Ormsby alignment comment block is still in the file")
    n = 0
    prev_es = None
    for pi, p in enumerate(doc.get("paragraphs", []), 1):
        for si, s in enumerate(p.get("sentences", []), 1):
            n += 1
            where = f"note {n} (para {pi}, sentence {si})"
            es = s.get("es", "")
            for k in ("literal", "ormsby"):
                if not s.get(k):
                    errs.append(f"{where}: empty {k}")
            if not s.get("vocab"):
                warns.append(f"{where}: no vocab")
            if not s.get("diagram"):
                errs.append(f"{where}: no diagram")
            if not s.get("forms"):
                errs.append(f"{where}: no forms")
            for v in s.get("vocab") or []:
                if not isinstance(v, dict) or not v.get("w") or not v.get("d"):
                    errs.append(f"{where}: vocab entry is not {{w, d}}: {v!r}")
            for f in s.get("forms") or []:
                if not isinstance(f, dict) or not f.get("w") or not f.get("f"):
                    errs.append(f"{where}: forms entry is not {{w, f}}: {f!r}")
                    continue
                fw = norm(f["w"])
                parts = [q.strip() for q in re.split(r"\.\.\.|, ", fw) if q.strip()]
                if not all(q in norm(es) for q in parts):
                    warns.append(f"{where}: forms word not in sentence: {f['w']!r}")
            walk(s.get("diagram") or [], es, prev_es, errs, where)
            blob = " ".join(str(x) for x in (
                s.get("literal"), s.get("note"), s.get("ormsby_note"),
                *(v.get("d", "") for v in s.get("vocab") or [] if isinstance(v, dict)),
                *(f.get("f", "") for f in s.get("forms") or [] if isinstance(f, dict)),
            ))
            diag_r = []
            def collect(nodes):
                for nd in nodes:
                    if isinstance(nd, dict):
                        diag_r.append(str(nd.get("r", "")))
                        collect(nd.get("under", []))
            collect(s.get("diagram") or [])
            blob += " " + " ".join(diag_r)
            for pat, why in FORBIDDEN:
                m = re.search(pat, blob, re.I)
                if m:
                    errs.append(f"{where}: {why}: ...{blob[max(0, m.start()-30):m.end()+30]}...")
            for pat, why in ORMSBY_NOTE_FORBIDDEN:
                if re.search(pat, str(s.get("ormsby_note") or "")):
                    errs.append(f"{where}: {why}")
            if s.get("ormsby_match") is False and not s.get("ormsby"):
                errs.append(f"{where}: ormsby_match false but no ormsby text")
            prev_es = es
    for k in ("summary", "context"):
        v = doc.get(k) or ""
        paras = [q for q in v.strip().split("\n\n") if q.strip()]
        if k == "summary" and not 2 <= len(paras) <= 6:
            warns.append(f"{k}: {len(paras)} paragraphs (expected 3 or 4)")
        if k == "context" and len(paras) < 3:
            warns.append(f"{k}: only {len(paras)} paragraphs")
        for pat, why in FORBIDDEN[:3]:
            if re.search(pat, v, re.I):
                errs.append(f"{k}: {why}")
    for w in warns:
        print("WARN", w)
    for e in errs:
        print("ERROR", e)
    print(("OK" if not errs else "FAIL") + f": {n} notes, {len(errs)} errors, {len(warns)} warnings")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main(sys.argv[1])
