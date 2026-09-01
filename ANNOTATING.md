# How to annotate a chapter

This is the editorial procedure used for Part I, Chapter 1. Follow it for every
later chapter so the notes stay consistent. `content/part1/ch01.yaml` is the
worked example; when this document and that file disagree, this document wins.

## 1. Make the skeleton

    make skeleton PART=1 CHAPTER_NUM=2

This slices the chapter out of `sources/pg2000.txt`, splits it into sentence
units, and writes `content/part1/ch02.skeleton.yaml` with the `es` fields filled
and everything else empty. Ormsby's paragraphs for the same chapter are appended
as a comment block for alignment. Rename the file to `ch02.yaml` once you start
filling it in, and delete the comment block before committing.

`make fetch PART=1 CHAPTER_NUM=2` also downloads the Standard Ebooks chapter file
(`sources/se-chapter-1-2.xhtml`), which you need for step 5.

## 2. Check the sentence units

The extractor splits on `.`, `!`, `?`. Units longer than about 50 words are
split again at `;` or `:`. Review the result by hand:

- Merge fragments that are too short to stand alone (fewer than about 8 words)
  into the preceding unit, unless they are a separate paragraph in the source.
- A unit that ends in `;` or `:` is fine. The body text reads unchanged; only
  the note markers are inserted.
- Dialogue paragraphs (starting with `—`) stay as their own paragraph. A
  paragraph is a paragraph in Gutenberg, never merge or split those.
- Very long units with no `;` or `:` (70+ words) are left whole. Do not split at
  commas.

Never edit Cervantes. The only changes allowed to `es` are typographic:
Gutenberg's `''...''` quotes become `«...»`, and whitespace is normalized.
`make verify` checks that the concatenated `es` fields still equal the Gutenberg
text paragraph by paragraph. It must pass before you build.

## 3. Ormsby

`ormsby` is the span of John Ormsby's translation that covers the same words.
Use the Standard Ebooks text (modernized names: Sigüenza, Quixote) rather than
the raw Gutenberg text when they differ.

- Ormsby's sentence boundaries often differ from Cervantes'. Cut his text at
  the point that matches the Spanish unit even if that is mid-sentence in
  English. Keep his punctuation at the cut.
- When a Spanish unit was split at `;`/`:` and Ormsby's rendering cannot be cut
  cleanly, put the whole English sentence on the first piece and, on the other
  pieces, the closest fragment with `ormsby_match: false`. The builder labels
  that "Ormsby (loose)".
- Ormsby's quotation marks: keep his curly quotes as they are.

## 4. Literal gloss

`literal` is a word-for-word gloss that keeps Spanish word order wherever the
result is still readable English. It is a crib, not a translation.

- Translate every word. The only Spanish left in a gloss is proper names of
  people, places, horses and books. `hidalgo` is "gentleman", `salpicón` is
  "cold-hash", `hanegas` is "acre-plots". The precise meaning goes in the
  vocabulary entry, not in the gloss.
- Words that are already English (morion, the coin real, olla when Ormsby
  keeps it) may stay.
- One Spanish word that needs several English words is hyphenated:
  `acordarme` → "to-remember-myself", `desvelábase` → "kept-himself-awake",
  `Llenósele` → "Filled-itself-to-him".
- Words English needs that Spanish omits go in square brackets:
  "not [it] has much time", "in the [matter] of the valor".
- Keep the Spanish order for adjectives and clitics ("buckler old", "him
  I-knock-down"). Reorder only when English becomes unparseable.
- Do not smooth idioms. "por malos de mis pecados" is "for bad of my sins";
  the vocabulary entry explains it.

## 5. Vocabulary

`vocab` is a list of `{w, d}` pairs in the order the words appear. Depth is
intermediate: the reader knows ser/estar, common nouns and regular verbs, and
does not need those.

Include:
- uncommon or literary words (enjuto, descomunal, holgarse);
- every archaic spelling the first time it appears in the chapter, with the
  modern form (mesmo = mismo, della = de ella, fermosura = hermosura, efeto,
  estraño, letura, celebro, recebir, priesa, luengo, ansí);
- idioms and set phrases (no ir en zaga, de claro en claro, a secas);
- false friends (complexión, industria, competencia, curiosidad);
- grammar the reader will trip on, once per chapter: enclitic pronouns on
  conjugated verbs (Llenósele), the -ra form used as a conditional (hiciera,
  diera), absolute participles (Puesto nombre), `ha` for `hace`;
- proper names from the romances of chivalry and history, with one line saying
  who they are (Amadís de Gaula, Bernardo del Carpio, Trapisonda).

Write `w` as the dictionary form, or the phrase as it appears when it is the
phrase that matters (`no dejar de`, `por ... que`). `d` is one line: meaning
first, then the nuance or the modern form. Use single quotes inside `d`.

Ormsby's translator notes: `sources/se-chapter-1-N.xhtml` shows where his note
references fall (`noteref-NN`), and `sources/se-endnotes.xhtml` has the text.
Copy the note verbatim into `ormsby_note` on the sentence it annotates, with
straight quotes and his em-dashes turned into commas or parentheses. Notes that
only say "See here" point into his preface; replace them with your own `note`.

`note` is optional and is for something the reader would miss that neither the
gloss nor the vocabulary carries: a pun, a genre convention, a medical or
social fact. Two sentences at most.

## 6. Summary and context

`summary` is three or four short paragraphs in English telling what happens.
Spoilers within the chapter are fine; nothing from later chapters.

`context` is the essay the Kindle pop-up shows after the summary. Cover, in
this order when relevant: social background (class, money, food, clothes),
the books and legends being parodied, the narrator's games, any medicine or
law or religion the text assumes, the names and their jokes, and a closing
paragraph on the Spanish itself (the archaisms and constructions seen in this
chapter). Draw on Ormsby's notes and introduction and say so when you do.
Paragraphs are separated by blank lines; the builder joins them with line
breaks because Kindle shows only the first block of a note.

## 7. Build and check

    make verify     # Spanish still matches Gutenberg
    make check      # builds dist/dq-p1c01.epub and runs epubcheck; must be clean
    make site       # assembles _site/ for the browser reader

Then send the EPUB to the Kindle and read the chapter there. The things that
have needed fixing on the device so far are in the git log.

## Not yet generalized

The build, the `site` target and `site/index.html` still assume one EPUB named
`dq-p1c01.epub`. Before adding a second chapter, change `make build` to pass
every `content/part*/ch*.yaml` to `tools/build_epub.py` (it already accepts
several) and rename the output.
