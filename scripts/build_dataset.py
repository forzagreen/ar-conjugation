#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build data/ from a checkout of the source repository (the private working
repository that holds the transcription and the Lua module).

    python3 scripts/build_dataset.py --source /path/to/source-checkout   # or AR_CONJUGATION_SOURCE=...

Reads, from the source checkout:

    tools/extraction/verified_models.json   the 462 hand-verified paradigms (forms as
                                            printed, 14 rows per tense, null = unread)
    fixtures/index.csv                      slug, model, flags, classification ids
    tools/extraction/underblock_forms.json  مصدر / اسم الفاعل / اسم المفعول under each table
    tools/extraction/page_models.json       Template-A pages (one abstract model each)
    tools/extraction/page_verbs.json        Template-B pages (two verbs each)
    tests/python/test_corpus_coverage.py    ACCOUNTED_NULLS, the deliberately empty cells

and writes data/json/verbs.json, data/jsonl/verbs.jsonl, data/csv/verbs.csv,
data/csv/conjugations.csv, data/jsonl/conjugations.jsonl and data/json/errata.json. Deterministic: same input,
same bytes. Every string is NFC.
"""
import argparse
import csv
import importlib.util
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# The book prints 14 rows per tense (أنتما twice); the dataset has 13 persons.
BOOK_ROWS = ["3ms", "3md", "3mp", "3fs", "3fd", "3fp", "2ms", "2d", "2mp", "2fs", "2d", "2fp", "1s", "1p"]
BOOK_IMP_ROWS = ["2ms", "2d", "2mp", "2fs", "2d", "2fp"]
PERSONS = ["3ms", "3md", "3mp", "3fs", "3fd", "3fp", "2ms", "2d", "2mp", "2fs", "2fp", "1s", "1p"]
IMP_PERSONS = ["2ms", "2d", "2mp", "2fs", "2fp"]
COLUMNS = ["past", "past_pass", "ind", "ind_pass", "imp"]
COLUMN_TENSE = {"past": ("past", "active"), "past_pass": ("past", "passive"),
                "ind": ("indicative", "active"), "ind_pass": ("indicative", "passive"),
                "imp": ("imperative", "active")}

# وزن → verb form and, for form I, the past~non-past vowels (module/ar-verb.lua:140-163).
WAZN_FORM = {
    "فعَل يفعُل": ("I", "a", "u"), "فعَل يفعِل": ("I", "a", "i"), "فعَل يفعَل": ("I", "a", "a"),
    "فعُل يفعُل": ("I", "u", "u"), "فعِل يفعَل": ("I", "i", "a"), "فعِل يفعِل": ("I", "i", "i"),
    "فعّل": ("II", None, None), "فاعل": ("III", None, None), "أفعل": ("IV", None, None),
    "تفعّل": ("V", None, None), "تفاعل": ("VI", None, None), "انفعل": ("VII", None, None),
    "افتعل": ("VIII", None, None), "افعلّ": ("IX", None, None), "استفعل": ("X", None, None),
    "افعالّ": ("XI", None, None), "افعوعل": ("XII", None, None), "افعوّل": ("XIII", None, None),
    "فعلل": ("Iq", None, None), "تفعلل": ("IIq", None, None), "افعنلل": ("IIIq", None, None),
    "افعللّ": ("IVq", None, None),
}

VERDICT_STATUS = {
    "exact": "agrees-with-module", "loose": "agrees-with-module",
    "variant, exact": "agrees-with-module", "variant, loose": "agrees-with-module",
    "DIFFERS": "differs-from-module", "module has none": "book-only", "book prints none": "none",
}

TATWEEL = "ـ"


def nfc(s):
    return unicodedata.normalize("NFC", s).replace(TATWEEL, "").strip()


def variants(cell):
    """A printed cell's forms: the book sets alternatives in one cell, separated by
    «،», a space, or parentheses (عُشَّ (اُعْشُشْ)). Order kept, duplicates dropped."""
    out = []
    for v in re.split(r"[\s،()]+", cell.strip()):
        v = nfc(v)
        if v and v not in out:
            out.append(v)
    return out


def cell_value(cell):
    vs = variants(cell)
    return vs[0] if len(vs) == 1 else vs


def column(values, rows, persons):
    """One tense column: {person: form | [forms]} keyed by the 13/5 persons, first
    occurrence of the duplicated أنتما row winning. Absent key = not printed / not
    read. Returns None when the column is entirely absent (the page has no such
    column at all)."""
    if not values or all(v is None for v in values):
        return None
    out = {}
    for person, form in zip(rows, values):
        if person in out or not form:
            continue
        out[person] = cell_value(form)
    return {p: out[p] for p in persons if p in out}


def load_source(src):
    def j(*parts):
        with open(os.path.join(src, *parts), encoding="utf-8") as f:
            return json.load(f)
    models = j("tools", "extraction", "verified_models.json")
    with open(os.path.join(src, "fixtures", "index.csv"), encoding="utf-8") as f:
        index = list(csv.DictReader(f))
    if len(models) != len(index):
        sys.exit("verified_models.json has %d entries, index.csv %d" % (len(models), len(index)))
    under = {e["slug"]: e for e in j("tools", "extraction", "underblock_forms.json")["entries"]}
    a_pages = {p["page"] for p in j("tools", "extraction", "page_models.json")}
    b_pages = {p["page"] for p in j("tools", "extraction", "page_verbs.json")}
    spec = importlib.util.spec_from_file_location(
        "test_corpus_coverage", os.path.join(src, "tests", "python", "test_corpus_coverage.py"))
    tcc = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.join(src, "tools", "bulk"))
    spec.loader.exec_module(tcc)
    return models, index, under, a_pages, b_pages, tcc.ACCOUNTED_NULLS


def source_info(label, entry, under_entry, a_pages, b_pages, has_passive):
    """Where the paradigm was read. `page` is the pdfimages index of the 6th-edition
    scan, `printed_page` the number on the page itself; the offset between them is
    not constant, so neither is ever computed from the other."""
    page = printed = None
    template = None
    if under_entry:
        page = under_entry["page"]
        printed = under_entry.get("printed_page")
        template = "A" if page in a_pages else ("B" if page in b_pages else None)
    m = re.search(r"\(p(\.?)(\d+)", label)
    if m:
        n = int(m.group(2))
        if m.group(1):          # "p.125" = printed page number
            printed = printed or n
        else:                   # "p176" = pdfimages index
            page = page or n
    if template is None and has_passive:
        template = "A"          # only Template-A pages print a passive
    return {"model": int(entry["model"]), "template": template, "page": page,
            "printed_page": printed, "label": nfc(label)}


def derived_info(u):
    if not u:
        return None
    def one(key):
        val = u.get(key)
        verdict = u.get(key + "_verdict") or "none"
        status = VERDICT_STATUS.get(verdict, verdict)
        return (nfc(val) if val else None), status, bool(u.get(key + "_read"))
    ap, ap_status, ap_read = one("ap")
    pp, pp_status, pp_read = one("pp")
    return {
        "masdar": [nfc(x) for x in (u.get("masdar") or []) if x],
        "active_participle": ap,
        "passive_participle": pp,
        "status": {"active_participle": ap_status, "passive_participle": pp_status},
        "read_from_page": {"active_participle": ap_read, "passive_participle": pp_read},
    }


def build_records(models, index, under, a_pages, b_pages):
    records = []
    for m, e in zip(models, index):
        slug = e["slug"]
        form, pv, npv = WAZN_FORM[m["wazn"]]
        conj = {
            "past": column(m.get("past"), BOOK_ROWS, PERSONS),
            "past_pass": column(m.get("past_pass"), BOOK_ROWS, PERSONS),
            "ind": column(m.get("ind"), BOOK_ROWS, PERSONS),
            "ind_pass": column(m.get("ind_pass"), BOOK_ROWS, PERSONS),
            "imp": column(m.get("imp"), BOOK_IMP_ROWS, IMP_PERSONS),
        }
        has_passive = conj["past_pass"] is not None or conj["ind_pass"] is not None
        lemma_cell = conj["past"].get("3ms") if conj["past"] else None
        lemma = lemma_cell[0] if isinstance(lemma_cell, list) else lemma_cell
        records.append({
            "id": slug,
            "lemma": lemma,
            "root": nfc(m["root"]),
            "wazn": nfc(m["wazn"]),
            "form": form,
            "vowels": {"past": pv, "nonpast": npv} if form == "I" else None,
            "flags": {"full_passive": bool(e["passive"]), "reduced": bool(e["reduced"])},
            "classification": {"root_type": int(e["root_type"]), "verb_type": e["verb_type"]},
            "source": source_info(m["label"], e, under.get(slug), a_pages, b_pages, has_passive),
            "conjugation": conj,
            "derived": derived_info(under.get(slug)),
        })
    return records


def errata(records, accounted_nulls):
    by_id = {r["id"]: r for r in records}
    nulls = []
    reasons = {
        ("309_147", "ind", "3fp"): "compositor slip: the page sets a neighbouring row's form in this cell",
        ("315_157", "ind", "3fp"): "compositor slip: the page sets a neighbouring row's form in this cell",
        ("317_157", "ind", "3fp"): "compositor slip: the page sets a neighbouring row's form in this cell",
        ("319_206", "ind", "3fp"): "compositor slip: the page sets a neighbouring row's form in this cell",
        ("347_267", "ind", "3fp"): "compositor slip: the page sets a neighbouring row's form in this cell",
        ("304_136", "past", "3fp"): "compositor slip: the page sets a neighbouring row's form in this cell",
        ("263_269", "ind", "3fp"): "the page contradicts its own page-mate (same model, facing page)",
        ("261_264", "ind", "3mp"): "the page contradicts its own page-mate (same model, facing page)",
        ("261_264", "ind", "2mp"): "the page contradicts its own page-mate (same model, facing page)",
        ("053_158", "imp", "2fs"): "blank on the page (ink measured)",
        ("277_288", "imp", "2ms"): "blank on the page (ink measured)",
        ("365_414", "imp", "2ms"): "blank on the page (ink measured)",
    }
    for slug, col, person in sorted(accounted_nulls):
        r = by_id[slug]
        nulls.append({"id": slug, "lemma": r["lemma"], "column": col, "person": person,
                      "reason": reasons.get((slug, col, person), "see fixtures/SOURCES.md upstream")})
    corrections = [
        {"id": "010_168", "lemma": by_id["010_168"]["lemma"], "column": "ind_pass", "persons": "all",
         "printed": "يُلَى / تُلَى …", "corrected": "يُولَى / تُولَى …",
         "reason": "the و is dropped throughout the passive non-past column; the book's own وَفَى page prints يُوفَى"},
        {"id": "008_146", "lemma": by_id["008_146"]["lemma"], "column": "past", "persons": "3fp",
         "printed": "هَيُؤْنا", "corrected": "هَيُؤْنَ",
         "reason": "byte-for-byte duplicate of the 1p cell; a 3fp past in ـنا is not valid morphology for any root"},
        {"id": "026_111", "lemma": by_id["026_111"]["lemma"], "column": "past_pass", "persons": "2fp",
         "printed": "مُدِدْتُنُّ", "corrected": "مُدِدْتُنَّ",
         "reason": "the active cell of the same page reads مَدَدْتُنَّ and no rule changes the suffix vowel between voices"},
        {"id": "031_125", "lemma": by_id["031_125"]["lemma"], "column": "past_pass", "persons": "3fs",
         "printed": "وَصِلَتْ", "corrected": "وُصِلَتْ",
         "reason": "the 13 sibling cells of the column print damma on the فاء"},
    ]
    conventions = [
        {"convention": "hamzat wasl written as bare alif or with the wasla sign",
         "example": "اُكْتُبْ = ٱكْتُبْ"},
        {"convention": "a hamza seat that already encodes the vowel may be printed without it",
         "example": "إدْ = إِدْ (وأد, p.174)"},
        {"convention": "a hamza with sukun after a damma: spelt out on a waw seat (تحقيق) or merged (تسهيل)",
         "example": "أُؤْكَلُ = أُوكَلُ (أكل p.133, أله p.175, أصل p.195)"},
        {"convention": "a hamza with sukun after a kasra-ed wasl alif: spelt on a ya seat or as ya",
         "example": "اِئْثِرْ = إِيْثِرْ (أثر p.151)"},
        {"convention": "the short vowel before its long counterpart may be written or left off",
         "example": "فَعَلَا = فَعَلا, decided per page and per class (see upstream SOURCES.md)"},
        {"convention": "a retained و or ي after its short vowel may carry an explicit sukun",
         "example": "يُوْصَلُ = يُوصَلُ (وصل p.155), اِيْقَظْ = اِيقَظْ (يقظ p.222)"},
        {"convention": "a final sukun may be omitted", "example": "يَفْعَلْ = يَفْعَل"},
    ]
    return {
        "_what": "What the dataset changes or leaves empty relative to the printed page, and the "
                 "printing conventions a comparison should ignore. Every item is documented at "
                 "length in the upstream fixtures/SOURCES.md.",
        "deliberately_empty_cells": nulls,
        "corrected_misprints": corrections,
        "printing_conventions": conventions,
    }


def write_json(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")


def write_jsonl(path, records):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")


def write_csvs(records):
    with open(os.path.join(ROOT, "data", "csv", "verbs.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["id", "lemma", "root", "wazn", "form", "past_vowel", "nonpast_vowel", "full_passive",
                    "reduced", "root_type", "verb_type", "model", "template", "page", "printed_page",
                    "masdar", "active_participle", "passive_participle"])
        for r in records:
            d = r["derived"] or {}
            v = r["vowels"] or {}
            s = r["source"]
            w.writerow([r["id"], r["lemma"], r["root"], r["wazn"], r["form"], v.get("past") or "",
                        v.get("nonpast") or "", int(r["flags"]["full_passive"]), int(r["flags"]["reduced"]),
                        r["classification"]["root_type"], r["classification"]["verb_type"], s["model"],
                        s["template"] or "", s["page"] or "", s["printed_page"] or "",
                        " ، ".join(d.get("masdar") or []), d.get("active_participle") or "",
                        d.get("passive_participle") or ""])
    n = 0
    header = ["id", "lemma", "root", "wazn", "form", "tense", "voice", "person", "variant", "text"]
    flat = []
    with open(os.path.join(ROOT, "data", "csv", "conjugations.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for r in records:
            for col in COLUMNS:
                cells = r["conjugation"][col]
                if not cells:
                    continue
                tense, voice = COLUMN_TENSE[col]
                for person in (IMP_PERSONS if col == "imp" else PERSONS):
                    if person not in cells:
                        continue
                    vals = cells[person]
                    for i, text in enumerate(vals if isinstance(vals, list) else [vals], 1):
                        row = [r["id"], r["lemma"], r["root"], r["wazn"], r["form"], tense, voice, person, i, text]
                        w.writerow(row)
                        flat.append(dict(zip(header, row)))
                        n += 1
    # the same table as JSON Lines: the Hugging Face viewer reads every config with one
    # builder, so the "cells" config cannot be CSV next to a JSON Lines default
    write_jsonl(os.path.join(ROOT, "data", "jsonl", "conjugations.jsonl"), flat)
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--source", default=os.environ.get("AR_CONJUGATION_SOURCE"),
                    help="path to the source checkout (or set AR_CONJUGATION_SOURCE)")
    args = ap.parse_args()
    if not args.source:
        ap.error("--source DIR is required (or set AR_CONJUGATION_SOURCE)")
    src = os.path.abspath(args.source)
    models, index, under, a_pages, b_pages, accounted_nulls = load_source(src)
    records = build_records(models, index, under, a_pages, b_pages)
    for d in ("json", "jsonl", "csv"):
        os.makedirs(os.path.join(ROOT, "data", d), exist_ok=True)
    write_json(os.path.join(ROOT, "data", "json", "verbs.json"), records)
    write_jsonl(os.path.join(ROOT, "data", "jsonl", "verbs.jsonl"), records)
    write_json(os.path.join(ROOT, "data", "json", "errata.json"), errata(records, accounted_nulls))
    n = write_csvs(records)
    print("%d paradigms, %d conjugation rows written to data/" % (len(records), n))


if __name__ == "__main__":
    main()
