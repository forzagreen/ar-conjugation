# ar-conjugation — technical details

## Files

```
data/json/verbs.json        462 records, the canonical form (pretty-printed, sorted as the book was read)
data/jsonl/verbs.jsonl      the same records, one JSON object per line
data/csv/conjugations.csv   one row per inflected form: id,lemma,root,wazn,form,tense,voice,person,variant,text
data/jsonl/conjugations.jsonl  the same rows as JSON objects (the Hugging Face "cells" config)
data/csv/verbs.csv          one row per paradigm: id,lemma,root,wazn,form,past_vowel,nonpast_vowel,full_passive,
                            reduced,root_type,verb_type,model,template,page,printed_page,masdar,
                            active_participle,passive_participle
data/json/errata.json       corrected misprints, deliberately empty cells, printing conventions
scripts/build_dataset.py    rebuilds data/ from a checkout of the private source repository
scripts/validate.py         shape, counts, NFC, csv/json agreement (CI)
scripts/push_hf.py          mirrors data/ + README to Hugging Face
scripts/serve.py            serves site/ locally with data/ mounted as on GitHub Pages
site/                       the browsing page
```

## Fields

| Field | Meaning |
|---|---|
| `id` | Stable identifier, `NNN_MMM`: reading order in the upstream corpus, then the book's model number. |
| `lemma` | The citation form: 3rd person masculine singular of the active past, as printed. |
| `root` | The root, bare letters. Hamza is always `ء`; a final ي covers both ي and ى. |
| `wazn` | The pattern, named the way Arabic grammar names it: form I carries its past and non-past vowels (`فعَل يفعُل`), the other forms their shape (`استفعل`). 22 values. |
| `form` | Western form number: `I`–`XIII` for triliteral verbs, `Iq`–`IVq` for quadriliteral. |
| `vowels` | Form I only: the past and non-past stem vowels, `a` / `i` / `u`. |
| `flags.full_passive` | The page prints a personal passive for persons other than 3ms. Set on 48 paradigms (an engine needs telling, since transitivity cannot be read off the root). |
| `flags.reduced` | The page prints the assimilated shape of an affix: forms V/VI with the تَ- assimilated into a coronal first radical (اِسَّمَّعَ for تَسَمَّعَ), form VII with the ن assimilated into م (اِمَّدَحَ), form IIIq with the ن assimilated into a weak ل1 (اِهْبَيَّخَ). 10 paradigms. |
| `classification.root_type` | Root-structure class id (1–55) per the scheme in the upstream `GLOSSARY.md` (Paper 1). |
| `classification.verb_type` | Augmentation code `[R]+A[-Fn]` per the upstream `GLOSSARY.md` (Paper 2): radicals + added letters, then the form within that group, e.g. `3+2-III`. |
| `source.model` | The book's own model number for the paradigm (its classification of the verb). |
| `source.template` | `A`: one of the book's 83 abstract-model pages, five columns (active and passive). `B`: one of the two-verb pages, three columns (active only). `null`: read from the 2nd edition before the page inventory existed and not determinable. |
| `source.page` | The page's index in the 6th-edition scan (pdfimages numbering). |
| `source.printed_page` | The page number printed on the page. The offset between the two is not constant (14 to 17), so neither is ever computed from the other; a `null` means it was not recorded. |
| `source.label` | The upstream fixture label, kept for traceability. |
| `conjugation.<column>` | `past`, `past_pass`, `ind` (المضارع المرفوع), `ind_pass`, `imp`. `null` = the page has no such column. Otherwise an object keyed by person; a person absent from it is a cell the page leaves blank or misprints (see errata). |
| `derived` | The block printed under the table: `masdar` (list, in the book's order), `active_participle`, `passive_participle`. `null` for the 28 paradigms read before that block was extracted. |
| `derived.status.*` | How the derived noun was checked. `agrees-with-module`: one OCR pass that agrees with the independent engine. `read-from-page` is not a status but the flag `read_from_page`: the cell was read by a person from the page image, at 4–14×. `differs-from-module`: the book's reading stands and the engine derives something else (6 cells, all explained upstream). `book-only`: the engine derives no such noun. `none`: the book prints none. |

## Person codes and cell values

`3ms 3md 3mp 3fs 3fd 3fp 2ms 2d 2mp 2fs 2fp 1s 1p` — third person first, as the book's tables run. The book prints أنتما twice (masculine and feminine dual, identical forms); the dataset has one gender-neutral `2d`. The imperative has the five second persons.

A cell is a string. Ten cells are a list of strings: the book prints two alternatives in one cell (اِئْتِ / اِيتِ, عُشَّ / اُعْشُشْ, يَرَى / يَرْأَى, …), in the book's order. In `conjugations.csv` these become two rows with `variant` 1 and 2.

Every string is Unicode NFC (so a vowel precedes a following shadda), contains only Arabic letters and marks, and carries no tatweel or bidi controls. `scripts/validate.py` enforces all of this.

## Errata

`errata.json` has three lists:

- `deliberately_empty_cells` (12): cells the page prints but the dataset leaves out, each with its reason — six compositor slips where the page sets a neighbouring row's form, three where a page contradicts its own facing page of the same model, three genuinely blank (ink measured).
- `corrected_misprints` (4): cells where the dataset departs from the printed page, with the printed form, the corrected one and why.
- `printing_conventions` (7): spellings the book alternates between that are not differences of form.

## Rebuilding

```bash
python3 scripts/build_dataset.py --source /path/to/source-checkout   # or AR_CONJUGATION_SOURCE=...
python3 scripts/validate.py
python3 scripts/serve.py          # http://localhost:8000/
HF_TOKEN=... uv run --with huggingface_hub scripts/push_hf.py
```

The build is deterministic; CI runs `validate.py` on every push, and `pages.yml` publishes `site/` with `data/` mounted beside it, so the site's download links serve the committed files.
