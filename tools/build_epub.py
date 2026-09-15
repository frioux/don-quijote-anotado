#!/usr/bin/env python3
"""Build an EPUB3 from one or more annotated chapter YAML files.

usage: build_epub.py chapter.yaml [chapter2.yaml ...] out.epub
"""
import datetime as dt
import html
import sys
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
BOOK_ID = "urn:uuid:7c3f2a1e-5b7d-4e4a-9a3f-0d0e00000001"
TITLE = "Don Quijote de la Mancha (edición anotada para angloparlantes)"

XHTML_HEAD = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{lang}" lang="{lang}">
<head>
<meta charset="utf-8"/>
<title>{title}</title>
<link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body epub:type="{btype}">
"""
XHTML_FOOT = "</body>\n</html>\n"


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def grammar_html(g: dict, br: str) -> str:
    """The grammar section of a note: a one-line map of the sentence, then
    each chunk of the Spanish with its analysis (conjugation, agreement,
    function words), in sentence order."""
    lines = ["<b>Grammar</b>"]
    if g.get("structure"):
        lines.append(esc(g["structure"]))
    for part in g.get("parts", []):
        lines.append(f'• <b xml:lang="es" lang="es">{esc(part["s"])}</b> — {esc(part["g"])}')
    return br.join(lines)


def chapter_xhtml(doc: dict, cid: str) -> str:
    title_es = doc["title_es"]
    head, _, sub = title_es.partition(". ")
    out = [XHTML_HEAD.format(lang="es", title=esc(head), btype="bodymatter chapter")]
    out.append(f'<section epub:type="chapter" id="{cid}">\n')
    out.append(f"<h2>{esc(head)}</h2>\n<p class=\"subtitle\">{esc(sub)}</p>\n")
    if doc.get("title_en"):
        out.append(f'<p class="subtitle" xml:lang="en" lang="en">{esc(doc["title_en"])}</p>\n')
    notes = []
    n = 0
    for p in doc["paragraphs"]:
        sents = p["sentences"]
        cls = ' class="dialogue"' if sents and sents[0]["es"].lstrip().startswith("—") else ""
        out.append(f"<p{cls}>")
        for s in sents:
            n += 1
            out.append(f'{esc(s["es"])}<a href="#n{n}" id="r{n}" epub:type="noteref" class="nr">{n}</a> ')
            notes.append((n, s))
        out[-1] = out[-1].rstrip()
        out.append("</p>\n")
    # Section-summary note, hung off a § marker after the last sentence.
    out[-1] = out[-1][:-len("</p>\n")]
    out.append(' <a href="#nS" id="rS" epub:type="noteref" class="nr">§</a></p>\n')
    out.append('<hr class="notes"/>\n<h3 class="notes" xml:lang="en" lang="en">Notas / Notes</h3>\n')
    out.append('<section class="notes" xml:lang="en" lang="en">\n')
    # Kindle pop-ups render only the FIRST block element of the note target,
    # so each note is exactly one <p>; sections are separated with <br/> and
    # the vocab "list" is bullets + line breaks inside that same paragraph.
    BR = "<br/>"
    for n, s in notes:
        parts = []
        if s.get("ormsby"):
            label = "Ormsby" if s.get("ormsby_match", True) else "Ormsby (loose)"
            parts.append(f"<b>{label}:</b> {esc(s['ormsby'])}")
        parts.append(f"<b>Literal:</b> {esc(s['literal'])}")
        if s.get("vocab"):
            items = BR.join(f'• <b xml:lang="es" lang="es">{esc(v["w"])}</b> — {esc(v["d"])}' for v in s["vocab"])
            parts.append(f"<b>Vocabulary</b>{BR}{items}")
        if s.get("grammar"):
            parts.append(grammar_html(s["grammar"], BR))
        if s.get("ormsby_note"):
            parts.append(f"<b>Ormsby's note:</b> {esc(s['ormsby_note'])}")
        if s.get("note"):
            parts.append(f"<b>Note:</b> {esc(s['note'])}")
        body = (BR + BR).join(parts)
        out.append(f'<aside id="n{n}" epub:type="footnote" class="fn">\n')
        out.append(f'<p><a href="#r{n}" class="back">{n}.</a> {body}</p>\n')
        out.append("</aside>\n")
    summary_paras = [esc(p.strip()) for p in doc.get("summary", "").strip().split("\n\n") if p.strip()]
    context_paras = [esc(p.strip()) for p in doc.get("context", "").strip().split("\n\n") if p.strip()]
    body = "<b>Chapter summary</b>" + BR + (BR + BR).join(summary_paras)
    if context_paras:
        body += BR + BR + "<b>Context</b>" + BR + (BR + BR).join(context_paras)
    out.append('<aside id="nS" epub:type="footnote" class="fn">\n')
    out.append(f'<p><a href="#rS" class="back">§</a> {body}</p>\n')
    out.append("</aside>\n</section>\n</section>\n")
    out.append(XHTML_FOOT)
    return "".join(out)


def title_xhtml(chapters) -> str:
    out = [XHTML_HEAD.format(lang="es", title=esc(TITLE), btype="frontmatter titlepage")]
    out.append('<section epub:type="titlepage">\n')
    out.append("<h1>Don Quijote de la Mancha</h1>\n<p class=\"subtitle\">Miguel de Cervantes Saavedra</p>\n")
    out.append('<p class="subtitle" xml:lang="en" lang="en">Annotated edition for English-speaking readers</p>\n')
    out.append('<div xml:lang="en" lang="en">\n')
    out.append("<p class=\"howto\"><b>How to read this book.</b> The text is Cervantes' original Spanish "
               "(Project Gutenberg #2000). Every sentence ends with a small number. Tap it for a note with "
               "four parts: John <b>Ormsby</b>'s 1885 translation of the same sentence, a word-for-word "
               "<b>literal</b> gloss that follows the Spanish order, a <b>vocabulary</b> list of the "
               "words an intermediate reader is likely to need, and a <b>grammar</b> breakdown that walks "
               "through the sentence clause by clause: how each verb is conjugated, what the small words "
               "(prepositions, pronouns, conjunctions) are doing, and how the pieces agree. Where Ormsby "
               "wrote a translator's note on that sentence it is included. The § mark at the end of a chapter opens a summary and a "
               "context note for the whole chapter.</p>\n")
    out.append("<p class=\"howto\">In the grammar section every verb is given as its infinitive with its "
               "meaning, then person and number (<i>1st sg.</i> = I, <i>2nd sg.</i> = you, <i>3rd sg.</i> = "
               "he, she, it, <i>1st pl.</i> = we, <i>2nd pl.</i> = you all, <i>3rd pl.</i> = they), tense and mood. "
               "Every note is self-contained: a conjugation pattern or a rule is written out in full wherever "
               "it matters, so no note ever sends you to another one.</p>\n")
    out.append("<p class=\"howto\">Archaic spellings are kept as Cervantes wrote them (<i>mesmo</i> for "
               "<i>mismo</i>, <i>della</i> for <i>de ella</i>, <i>fermosura</i> for <i>hermosura</i>) and are "
               "glossed the first time they matter. Long-press any Spanish word for the Kindle dictionary.</p>\n")
    out.append("<p class=\"howto\">Contents: " + "; ".join(esc(c["title_es"].split(". ")[0]) for c in chapters) + ".</p>\n")
    out.append("</div>\n</section>\n")
    out.append(XHTML_FOOT)
    return "".join(out)


def nav_xhtml(items) -> str:
    out = [XHTML_HEAD.format(lang="es", title="Índice", btype="frontmatter toc")]
    out.append('<nav epub:type="toc" id="toc">\n<h2>Índice</h2>\n<ol>\n')
    out.append('<li><a href="title.xhtml">Portada</a></li>\n')
    for fname, label in items:
        out.append(f'<li><a href="{fname}">{esc(label)}</a></li>\n')
    out.append("</ol>\n</nav>\n")
    out.append('<nav epub:type="landmarks" hidden="hidden">\n<ol>\n')
    out.append('<li><a epub:type="titlepage" href="title.xhtml">Portada</a></li>\n')
    out.append(f'<li><a epub:type="bodymatter" href="{items[0][0]}">Texto</a></li>\n')
    out.append("</ol>\n</nav>\n")
    out.append(XHTML_FOOT)
    return "".join(out)


def ncx(items) -> str:
    pts = []
    order = 1
    pts.append(f'<navPoint id="np{order}" playOrder="{order}"><navLabel><text>Portada</text></navLabel><content src="title.xhtml"/></navPoint>')
    for fname, label in items:
        order += 1
        pts.append(f'<navPoint id="np{order}" playOrder="{order}"><navLabel><text>{esc(label)}</text></navLabel><content src="{fname}"/></navPoint>')
    return f"""<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="es">
<head><meta name="dtb:uid" content="{BOOK_ID}"/><meta name="dtb:depth" content="1"/>
<meta name="dtb:totalPageCount" content="0"/><meta name="dtb:maxPageNumber" content="0"/></head>
<docTitle><text>{esc(TITLE)}</text></docTitle>
<navMap>{''.join(pts)}</navMap>
</ncx>
"""


def opf(items) -> str:
    modified = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest = [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
        '<item id="css" href="style.css" media-type="text/css"/>',
        '<item id="title" href="title.xhtml" media-type="application/xhtml+xml"/>',
    ]
    spine = ['<itemref idref="title"/>']
    for i, (fname, _) in enumerate(items):
        manifest.append(f'<item id="c{i}" href="{fname}" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="c{i}"/>')
    return f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="es">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="bookid">{BOOK_ID}</dc:identifier>
<dc:title>{esc(TITLE)}</dc:title>
<dc:language>es</dc:language>
<dc:language>en</dc:language>
<dc:creator id="cr">Miguel de Cervantes Saavedra</dc:creator>
<dc:contributor id="tr">John Ormsby</dc:contributor>
<meta refines="#tr" property="role" scheme="marc:relators">trl</meta>
<dc:date>1605</dc:date>
<dc:rights>Spanish text and Ormsby translation are in the public domain. Annotations for this edition.</dc:rights>
<meta property="dcterms:modified">{modified}</meta>
</metadata>
<manifest>
{chr(10).join(manifest)}
</manifest>
<spine toc="ncx">
{chr(10).join(spine)}
</spine>
</package>
"""


def main(argv):
    *yamls, out = argv
    chapters = [yaml.safe_load(Path(y).read_text(encoding="utf-8")) for y in yamls]
    items = []
    files = {}
    for doc in chapters:
        cid = f"p{doc['part']}c{doc['chapter']:02d}"
        fname = f"{cid}.xhtml"
        files[fname] = chapter_xhtml(doc, cid)
        items.append((fname, doc["title_es"].split(". ")[0]))
    with zipfile.ZipFile(out, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", """<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="OEBPS/package.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>
""", compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/package.opf", opf(items), compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/nav.xhtml", nav_xhtml(items), compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/toc.ncx", ncx(items), compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/style.css", (ROOT / "tools/style.css").read_text(encoding="utf-8"), compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/title.xhtml", title_xhtml(chapters), compress_type=zipfile.ZIP_DEFLATED)
        for fname, content in files.items():
            z.writestr(f"OEBPS/{fname}", content, compress_type=zipfile.ZIP_DEFLATED)
    print(f"wrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:])
