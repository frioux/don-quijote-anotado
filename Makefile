PY ?= python3
CHAPTER ?= content/part1/ch01.yaml
OUT ?= dist/dq-p1c01.epub

.PHONY: fetch skeleton build check verify site clean

fetch:
	mkdir -p sources
	curl -sL https://www.gutenberg.org/cache/epub/2000/pg2000.txt | tr -d '\r' > sources/pg2000.txt
	curl -sL https://www.gutenberg.org/cache/epub/996/pg996.txt | tr -d '\r' > sources/pg996.txt
	curl -sL https://raw.githubusercontent.com/standardebooks/miguel-de-cervantes-saavedra_don-quixote_john-ormsby/master/src/epub/text/endnotes.xhtml -o sources/se-endnotes.xhtml
	curl -sL https://raw.githubusercontent.com/standardebooks/miguel-de-cervantes-saavedra_don-quixote_john-ormsby/master/src/epub/text/chapter-1-1.xhtml -o sources/se-chapter-1-1.xhtml

skeleton:
	$(PY) tools/extract_chapter.py --part 1 --chapter 1 --out content/part1/ch01.skeleton.yaml

build:
	mkdir -p dist
	$(PY) tools/build_epub.py $(CHAPTER) $(OUT)

check: build
	epubcheck $(OUT)

verify:
	$(PY) tools/verify_text.py $(CHAPTER)

clean:
	rm -rf dist _site

# Static site for GitHub Pages: the viewer page plus the built EPUB.
site: build
	rm -rf _site && mkdir -p _site
	cp site/index.html _site/
	cp $(OUT) _site/
