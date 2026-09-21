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

## 6. Diagram and forms

Two sections after the vocabulary take the sentence apart for a reader who
wants to learn the Spanish, not just decode it: a `diagram` of how the phrases
hang together, and a `forms` list that shows what happened to every word that
was conjugated or made to agree.

    diagram:
      - s: "vivía"
        r: "main verb: lived"
        under:
          - s: "un hidalgo"
            r: "subject: who lived"
            under:
              - {s: "de los de lanza en astillero, ...", r: "what kind of hidalgo"}
          - {s: "no ha mucho tiempo que", r: "when: not long ago"}
    forms:
      - {w: "vivía", f: "viv- + -ía → vivir (to live), imperfect, he/she/it: 'was living'. The imperfect of -er and -ir verbs: -ía, -ías, -ía, -íamos, -íais, -ían."}

### Diagram

`diagram` is a tree. Each node is `s`, a chunk quoted exactly as Cervantes
wrote it, `r`, its role in a few words, and optionally `under`, the chunks that
attach to it. The builder renders it as an indented list, one line per node,
four spaces deeper for each level.

- The root is the main verb (or the first few words containing it). A sentence
  with two or three main clauses has two or three roots. A fragment that
  continues the previous sentence (`que no era caballero melindroso ...`)
  takes its root from the previous sentence (`decía`) and says so in `r`.
- Under the verb go its subject, its objects, and its adverbials, in text
  order. Under a noun go the phrases and relative clauses that describe it.
  A result or purpose clause goes under the phrase that triggers it (`de tal
  manera` → `que ...`).
- `r` is a label, not an analysis: `subject`, `object`, `where`, `when`,
  `why`, `how`, `describes 'lugar'`, `condition`, `result`, `what he said, 2`.
  Add a short English paraphrase after a colon when the chunk is long.
- Keep clauses whole. A relative clause with its own verb is one leaf; its
  verb is explained in `forms`. Aim for five to ten nodes; the long sentences
  take fifteen.
- Every `s` must be a verbatim substring of `es` (or of the previous
  sentence, for a carried-over root). Do not glue a conjunction onto a verb it
  is not adjacent to; put the conjunction in `r` instead (`main verb 2 (after
  'y')`).

### Forms

`forms` is a list of `{w, f}` pairs in text order. `w` is the word exactly as
it appears (with its clitics: `Llenósele`, `acomodársele`), or a short group
that shares one explanation (`los sábados`, `seco, enjuto`). `f` is one or two
sentences in this shape:

    stem + ending → dictionary form (meaning), tense, person: 'gloss'. Paradigm or rule.

- Conjugated verbs: `perd- + -ía → perder (to lose), imperfect, he`. Person is
  a plain pronoun (I, he, she, it, they, one), never `3rd sg.` Name the tense
  in plain words: present, preterite, imperfect, conditional, future,
  pluperfect, present subjunctive, imperfect subjunctive (-ra form / -se form).
- Then the six endings of that tense, every time the tense appears in a note:
  `The imperfect of -ar verbs: -aba, -abas, -aba, -ábamos, -abais, -aban.`
  For an irregular verb, the six forms instead: `vine, viniste, vino, ...`.
  When a second word in the same note uses the same tense, `Same -aba
  imperfect.` is enough. Never send the reader to another note.
- Enclitics: `desvel- + -aba + se → desvelar (to keep awake) with 'se' stuck
  on the end; modern 'se desvelaba'`, with the one-line rule about Cervantes
  hanging pronouns on a clause-opening verb.
- Infinitives, gerunds, participles: what they come from and what governs
  them (`infinitive after 'para'`, `gerund of poner + 'se', accent added`).
- Agreement: `reci- + -a → recio (sturdy), feminine to match 'complexión'`;
  `sus = plural to match 'pantuflos', not the owner`. Include demonstratives,
  possessives, apocope (`gran`, `buen`, `algún`), plurals with a spelling
  change (`veces`, `rocines`), suffixes (`-dor`, `-ón`, `-mente`, `-ísimo`).
- Contractions and archaic spellings: `della = de + ella`, `letura =
  lectura`, `mesmo = mismo`.
- Clitic pairs and function words only when their form is the point: `se lo`
  (le → se before lo), `le` as leísmo, `sí` with the accent, `al`, `del`.
- Leave out articles, plain nouns, and adjectives that do nothing
  interesting. Nouns and their meanings belong in `vocab`.

Use single quotes inside `r` and `f`. Never name a verb by a bare infinitive:
it is always `querer (to want)`, so the reader is never sent to the dictionary
by the note that is supposed to explain the sentence.

## 7. Summary and context

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

## 8. Build and check

    make verify     # Spanish still matches Gutenberg
    make check      # builds dist/don-quijote-anotado.epub from every chapter; epubcheck must be clean
    make site       # assembles _site/ for the browser reader

Then send the EPUB to the Kindle and read the chapter there. The things that
have needed fixing on the device so far are in the git log.

Every `content/part*/ch*.yaml` goes into the one EPUB; a new chapter is picked up
by the build as soon as the file exists.
