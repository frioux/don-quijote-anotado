# Don Quijote, annotated for English-speaking learners of Spanish

An EPUB whose body is Cervantes' original Spanish. Every sentence carries a
footnote with a word-for-word gloss, John Ormsby's 1885 English translation of
the same sentence, and a vocabulary list. Each chapter ends with a summary and
context note. Built for Kindle (pop-up footnotes) but standard EPUB3.

Status: pilot. Part I, Chapter 1 only.

## Build

    make fetch      # download sources into sources/ (already committed)
    make skeleton   # tools/extract_chapter.py -> content/partN/chNN.yaml skeleton
    make build      # tools/build_epub.py -> dist/dq-p1c01.epub
    make check      # epubcheck (brew install epubcheck)
    make verify     # confirm the Spanish body still matches Gutenberg verbatim

Requirements: Python 3.9+, PyYAML, epubcheck.

## Layout

    content/part1/ch01.yaml   annotated chapter (hand-authored)
    tools/extract_chapter.py  slices a chapter out of the sources into a skeleton YAML
    tools/build_epub.py       YAML -> EPUB3
    tools/verify_text.py      YAML Spanish == Gutenberg Spanish
    tools/style.css           reader stylesheet
    sources/                  raw public-domain sources, see SOURCES.md

## Reading it on a Kindle

Send `dist/dq-p1c01.epub` via <https://www.amazon.com/sendtokindle> or your
Send-to-Kindle email address. Tap a superscript number to open the note;
long-press a Spanish word for the Kindle Spanish dictionary.
