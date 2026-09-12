#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check data/ for shape, counts and internal consistency. Runs in CI.

    python3 scripts/validate.py

No network, no upstream checkout: everything is checked against the committed
files themselves and against the counts this dataset claims.
"""
import csv
import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

PERSONS = ["3ms", "3md", "3mp", "3fs", "3fd", "3fp", "2ms", "2d", "2mp", "2fs", "2fp", "1s", "1p"]
IMP_PERSONS = ["2ms", "2d", "2mp", "2fs", "2fp"]
COLUMNS = ["past", "past_pass", "ind", "ind_pass", "imp"]
FORMS = {"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "Iq", "IIq", "IIIq", "IVq"}
ARABIC = re.compile(r"^[ء-يً-ْٰٱ]+$")
BAD = re.compile("[​-‏‪-‮⁦-⁩ـ]")

EXPECTED_PARADIGMS = 495
EXPECTED_CELLS = 16593

fails = []


def check(ok, label, detail=""):
    print(("ok   " if ok else "FAIL ") + label + (("\n     " + detail) if (detail and not ok) else ""))
    if not ok:
        fails.append(label)


def forms_of(cell):
    return cell if isinstance(cell, list) else [cell]


def main():
    with open(os.path.join(DATA, "json", "verbs.json"), encoding="utf-8") as f:
        verbs = json.load(f)
    with open(os.path.join(DATA, "jsonl", "verbs.jsonl"), encoding="utf-8") as f:
        jsonl = [json.loads(line) for line in f if line.strip()]
    check(len(verbs) == EXPECTED_PARADIGMS, "%d paradigms" % EXPECTED_PARADIGMS, "got %d" % len(verbs))
    check(jsonl == verbs, "verbs.jsonl is verbs.json line by line")
    ids = [v["id"] for v in verbs]
    check(len(set(ids)) == len(ids), "ids are unique")

    cells = 0
    bad_forms = []
    for v in verbs:
        for key in ("id", "lemma", "root", "wazn", "form", "vowels", "flags", "classification", "source",
                    "conjugation", "derived"):
            if key not in v:
                fails.append("missing key %s in %s" % (key, v.get("id")))
        if v["form"] not in FORMS:
            fails.append("bad form %s in %s" % (v["form"], v["id"]))
        if (v["form"] == "I") != (v["vowels"] is not None):
            fails.append("vowels present iff form I: %s" % v["id"])
        conj = v["conjugation"]
        if set(conj) != set(COLUMNS):
            fails.append("columns of %s: %s" % (v["id"], sorted(conj)))
        for col in COLUMNS:
            block = conj[col]
            if block is None:
                continue
            persons = IMP_PERSONS if col == "imp" else PERSONS
            if list(block) != [p for p in persons if p in block]:
                fails.append("person order in %s/%s" % (v["id"], col))
            for person, cell in block.items():
                cells += 1
                for form in forms_of(cell):
                    if unicodedata.normalize("NFC", form) != form or BAD.search(form) or not ARABIC.match(form):
                        bad_forms.append((v["id"], col, person, form))
        if v["conjugation"]["past"] is None or "3ms" not in v["conjugation"]["past"]:
            fails.append("no past 3ms in %s" % v["id"])
        else:
            if v["lemma"] != forms_of(v["conjugation"]["past"]["3ms"])[0]:
                fails.append("lemma is not past 3ms in %s" % v["id"])
        for form in [v["lemma"], v["root"]] + ((v["derived"] or {}).get("masdar") or []):
            if unicodedata.normalize("NFC", form) != form or BAD.search(form):
                bad_forms.append((v["id"], "-", "-", form))
    check(not fails, "record shape", "; ".join(fails[:5]))
    check(cells == EXPECTED_CELLS, "%d printed cells" % EXPECTED_CELLS, "got %d" % cells)
    check(not bad_forms, "every form is NFC, Arabic-only, free of bidi marks and tatweel",
          "; ".join("%s %s/%s %r" % b for b in bad_forms[:5]))

    with open(os.path.join(DATA, "csv", "conjugations.csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    by_id = {v["id"]: v for v in verbs}
    mism = 0
    seen = set()
    for r in rows:
        v = by_id.get(r["id"])
        col = {("past", "active"): "past", ("past", "passive"): "past_pass", ("indicative", "active"): "ind",
               ("indicative", "passive"): "ind_pass", ("imperative", "active"): "imp"}[(r["tense"], r["voice"])]
        cell = v and v["conjugation"][col] and v["conjugation"][col].get(r["person"])
        want = forms_of(cell)[int(r["variant"]) - 1] if cell and len(forms_of(cell)) >= int(r["variant"]) else None
        if want != r["text"]:
            mism += 1
        seen.add((r["id"], col, r["person"]))
    check(mism == 0, "conjugations.csv agrees with verbs.json cell by cell", "%d mismatches" % mism)
    check(len(seen) == cells, "conjugations.csv covers every cell", "%d of %d" % (len(seen), cells))
    with open(os.path.join(DATA, "jsonl", "conjugations.jsonl"), encoding="utf-8") as f:
        flat = [json.loads(line) for line in f if line.strip()]
    check([{k: str(v) for k, v in d.items()} for d in flat] == rows,
          "conjugations.jsonl is conjugations.csv row by row")

    with open(os.path.join(DATA, "csv", "verbs.csv"), encoding="utf-8") as f:
        vrows = list(csv.DictReader(f))
    check([r["id"] for r in vrows] == ids, "verbs.csv lists the same paradigms in the same order")

    with open(os.path.join(DATA, "json", "errata.json"), encoding="utf-8") as f:
        err = json.load(f)
    empties = err["deliberately_empty_cells"]
    still_empty = all(by_id[e["id"]]["conjugation"][e["column"]] is not None and
                      e["person"] not in by_id[e["id"]]["conjugation"][e["column"]] for e in empties)
    check(still_empty, "every deliberately empty cell is still empty (%d)" % len(empties))
    corr = err["corrected_misprints"]
    check(all(c["id"] in by_id for c in corr), "every corrected misprint names a paradigm (%d)" % len(corr))

    print()
    if fails:
        print("%d check(s) failed" % len(fails))
        sys.exit(1)
    print("all checks passed")


if __name__ == "__main__":
    main()
