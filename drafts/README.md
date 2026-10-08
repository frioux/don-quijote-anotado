# Unfinished chapter annotations

These chapters were partly annotated and then stopped. They are kept out of
`content/` so the build only picks up finished chapters. Each file has every
field filled for the paragraphs it covers, and the remaining paragraphs are
missing. None of them has a summary or context yet.

| File | Done |
|---|---|
| part1-ch33.yaml | 19 of 32 paragraphs |
| part1-ch34.yaml | 44 of 62 paragraphs |
| part1-ch39.yaml | 9 of 19 paragraphs |
| part1-ch40.yaml | 10 of 29 paragraphs |

To finish one, move it to `content/part1/chNN.yaml`, follow ANNOTATING.md from
the first missing paragraph (`make skeleton` gives the Spanish units), and run
`make verify`, `tools/lint_chapter.py` and `make check`.
