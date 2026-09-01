PY ?= python3
PART ?= 1
CHAPTER_NUM ?= 1
CHAPTER ?= content/part$(PART)/ch$(shell printf %02d $(CHAPTER_NUM)).yaml
OUT ?= dist/dq-p1c01.epub

.PHONY: fetch skeleton build check verify site clean

fetch:
	mkdir -p sources
	curl -sL https://www.gutenberg.org/cache/epub/2000/pg2000.txt | tr -d '\r' > sources/pg2000.txt
	curl -sL https://www.gutenberg.org/cache/epub/996/pg996.txt | tr -d '\r' > sources/pg996.txt
	curl -sL https://raw.githubusercontent.com/standardebooks/miguel-de-cervantes-saavedra_don-quixote_john-ormsby/master/src/epub/text/endnotes.xhtml -o sources/se-endnotes.xhtml
	curl -sL https://raw.githubusercontent.com/standardebooks/miguel-de-cervantes-saavedra_don-quixote_john-ormsby/master/src/epub/text/chapter-$(PART)-$(CHAPTER_NUM).xhtml -o sources/se-chapter-$(PART)-$(CHAPTER_NUM).xhtml

skeleton:
	mkdir -p content/part$(PART)
	$(PY) tools/extract_chapter.py --part $(PART) --chapter $(CHAPTER_NUM) --out content/part$(PART)/ch$(shell printf %02d $(CHAPTER_NUM)).skeleton.yaml

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
