# Don Quijote, annotated for English-speaking learners of Spanish

An EPUB whose body is Cervantes' original Spanish. Every sentence carries a
footnote with a word-for-word gloss, John Ormsby's 1885 English translation of
the same sentence, a vocabulary list, and a grammar breakdown of the sentence
(conjugations, function words, agreement, word order). Each chapter ends with a summary and
context note. Built for Kindle (pop-up footnotes) but standard EPUB3.

Status: pilot. Part I, Chapter 1 only.

Read it in the browser: <https://frioux.github.io/don-quijote-anotado/> (the same EPUB, rendered with epub.js; tap a number for the note). The EPUB itself is built and published by GitHub Actions on every push.

## Build

    make fetch      # download sources into sources/ (already committed)
    make skeleton PART=1 CHAPTER_NUM=2   # skeleton YAML for a chapter
    make build      # all content/part*/ch*.yaml -> dist/don-quijote-anotado.epub
    make check      # epubcheck (brew install epubcheck)
    make verify     # confirm the Spanish body still matches Gutenberg verbatim
    make site       # assemble _site/ (viewer page + EPUB) for GitHub Pages

Requirements: Python 3.9+, PyYAML, epubcheck.

The editorial rules for filling in a chapter are in ANNOTATING.md.

## Layout

    content/part1/ch01.yaml   annotated chapter (hand-authored)
    tools/extract_chapter.py  slices a chapter out of the sources into a skeleton YAML
    tools/build_epub.py       YAML -> EPUB3
    tools/verify_text.py      YAML Spanish == Gutenberg Spanish
    tools/style.css           reader stylesheet
    sources/                  raw public-domain sources, see SOURCES.md
    site/index.html           browser reader for GitHub Pages (epub.js)
    .github/workflows/        builds, validates and deploys on push

## Reading it on a Kindle

Send `dist/don-quijote-anotado.epub` via <https://www.amazon.com/sendtokindle> or your
Send-to-Kindle email address. Tap a superscript number to open the note;
long-press a Spanish word for the Kindle Spanish dictionary.
