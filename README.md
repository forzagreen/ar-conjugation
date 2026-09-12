---
language:
- ar
pretty_name: Arabic verb conjugation tables (ar-verbs)
tags:
- arabic
- morphology
- conjugation
- verbs
- linguistics
size_categories:
- 10K<n<100K
configs:
- config_name: default
  data_files: jsonl/verbs.jsonl
- config_name: cells
  data_files: csv/conjugations.csv
---

# ar-verbs — Arabic verb conjugation tables

<div dir="rtl">

**جداول تصريف الأفعال العربية**: 462 نموذجًا مصرَّفًا (15,549 خانة) منقولةً من معجم تصريف الأفعال العربية لأنطوان الدحداح، مع المصدر واسم الفاعل واسم المفعول لكلّ فعل، وقد رُوجعت كلُّ خانة منها. يغطّي المجموعُ الأوزانَ الثلاثيةَ المجرّدة والمزيدة كلَّها والرباعيةَ، صحيحَها ومعتلَّها ومهموزَها ومضاعفَها.

</div>

A reference dataset of **462 fully conjugated Arabic verb paradigms** — **15,549 inflected forms** — transcribed from the standard reference on the subject, أنطوان الدحداح, *معجم تصريف الأفعال العربية* (Antoine El-Dahdah, *A Dictionary of Arabic Verb Conjugation*, Librairie du Liban, 6th ed. 2007), and verified cell by cell. Every form was checked against an independent conjugation engine ([`Module:ar-verb`](https://ar.wiktionary.org/wiki/وحدة:ar-verb) on Arabic Wiktionary); the two agree on all 15,549 cells, and the handful of misprints found in the book along the way are documented in `data/json/errata.json`.

🔗 **Browse it:** <https://forzagreen.github.io/ar-verbs> · **Hugging Face:** <https://huggingface.co/datasets/forzagreen/ar-verbs>

## What is in it

| | |
|---|---|
| Paradigms | **462** (366 distinct roots, 150 of the book's model numbers) |
| Inflected forms | **15,549** — the active past, active indicative and imperative of every verb; the passive past and passive indicative of the 48 verbs the book gives a passive for |
| Verb forms (أوزان) | all 6 vowel patterns of form I, forms II–XIII, and the four quadriliteral forms (Iq–IVq): 22 patterns |
| Root classes | sound, hamzated (initial, medial, final), geminate, assimilated (و and ي), hollow, defective, doubly weak, quadriliteral |
| Derived nouns | مصدر (676 verbal nouns), اسم الفاعل (426) and اسم المفعول (318) for 434 of the paradigms |
| Persons | 13 per tense: 3ms 3md 3mp 3fs 3fd 3fp 2ms 2d 2mp 2fs 2fp 1s 1p |

Each form is fully vocalised (every short vowel, shadda and sukun), stored in Unicode NFC, exactly as the book prints it — its spelling conventions included (see *Conventions* below).

## Download

| Format | File | Shape |
|---|---|---|
| JSON | [`data/json/verbs.json`](data/json/verbs.json) | one nested record per paradigm (canonical) |
| JSON Lines | [`data/jsonl/verbs.jsonl`](data/jsonl/verbs.jsonl) | same records, one per line |
| CSV | [`data/csv/conjugations.csv`](data/csv/conjugations.csv) | one row per inflected form |
| CSV | [`data/csv/verbs.csv`](data/csv/verbs.csv) | one row per paradigm: metadata, lemma, derived nouns |
| JSON | [`data/json/errata.json`](data/json/errata.json) | corrected misprints, deliberately empty cells, printing conventions |

```python
from datasets import load_dataset
verbs = load_dataset("forzagreen/ar-verbs")            # 462 paradigms
cells = load_dataset("forzagreen/ar-verbs", "cells")   # 15,559 rows (one per form, variants included)
```

## Record shape

```jsonc
{
  "id": "431_126",
  "lemma": "جاءَ",
  "root": "جيأ",
  "wazn": "فعَل يفعِل",                       // the pattern name, as Arabic grammar names it
  "form": "I",                               // I … XIII, Iq … IVq
  "vowels": {"past": "a", "nonpast": "i"},   // form I only
  "flags": {"full_passive": false, "reduced": false},
  "classification": {"root_type": 26, "verb_type": "3+0-II"},
  "source": {"model": 126, "template": "B", "page": 176, "printed_page": 159, "label": "جاءَ (p176)"},
  "conjugation": {
    "past":      {"3ms": "جاءَ", "3md": "جاءا", "3mp": "جاؤُوا", …},
    "past_pass": null,                       // the page has no passive column
    "ind":       {"3ms": "يَجيءُ", …},
    "ind_pass":  null,
    "imp":       {"2ms": "جِئْ", "2d": "جيئا", "2mp": "جيئُوا", "2fs": "جيئي", "2fp": "جِئْنَ"}
  },
  "derived": {
    "masdar": ["جَيْءٌ", "مَجِيءٌ"],
    "active_participle": "جاءٍ",
    "passive_participle": "مَجِيءٌ",
    "status": {"active_participle": "agrees-with-module", "passive_participle": "agrees-with-module"},
    "read_from_page": {"active_participle": false, "passive_participle": false}
  }
}
```

A cell is a string, or a list of strings where the book prints two alternatives in one cell (10 cells). A person missing from a column is a cell the page leaves blank or misprints (all twelve such cells are listed in `errata.json`). The full field reference, the person codes, the meaning of the flags and the provenance fields are in [`docs/DETAILS.md`](docs/DETAILS.md).

## Conventions

The forms are the book's own spelling. The book's typesetting varies on a few points that are not differences of form, and any comparison against another source should ignore them: the short vowel before a long vowel of the same quality may be written or left off (فَعَلَا / فَعَلا); a hamzat wasl may carry the wasla sign or not; a hamza with sukun after a damma or a kasra may be spelt on its seat (أُؤْكَلُ, اِئْثِرْ) or merged (أُوكَلُ, إِيْثِرْ); a retained و or ي may carry an explicit sukun (يُوْصَلُ); a final sukun may be omitted. The list, with the pages that attest each, is in `errata.json`.

## What is not in it

Only inflected forms and derived nouns — linguistic facts — are taken from the book. Its prose, explanatory notes, layout and page images are not reproduced. The subjunctive and jussive are not printed by the book and are therefore not here; a conjugation engine that generates them (and everything else) is published alongside this dataset as [`mazini`](https://github.com/forzagreen/mazini) (Python) and [`mazini-js`](https://github.com/forzagreen/mazini-js) (JavaScript), both tested against every cell of this dataset.

## Source

أنطوان الدحداح، **معجم تصريف الأفعال العربية، زائد بفهرس تصنيفي بالأفعال**، مكتبة لبنان ناشرون، الطبعة السادسة، 2007 (601 pp.), reviewed by د. جورج متري عبد المسيح. The first 25 paradigms were read from the 2nd edition (1995); the two editions' tables are the same text.

The transcription, verification and the engine it was verified against live in [`ar-wiktionary-modules`](https://github.com/forzagreen/ar-wiktionary-modules); `scripts/build_dataset.py` rebuilds `data/` from that checkout.

## Citation

```bibtex
@misc{arverbs2026,
  title  = {ar-verbs: Arabic verb conjugation tables},
  author = {Tellat, Wael},
  year   = {2026},
  url    = {https://github.com/forzagreen/ar-verbs}
}
```
