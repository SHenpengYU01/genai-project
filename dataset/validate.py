"""Validate task JSON files against the dataset schema (structural checks).

Run:  python dataset/validate.py
Exit: 0 all files structurally valid, 1 otherwise.
"""
import json
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(HERE, "tasks")

REQUIRED_TOP = ["id", "source", "difficulty", "title", "pou", "requirement",
                "interface", "ltl_specs", "test_cases", "reference"]


def check_task(t):
    errs = []
    for k in REQUIRED_TOP:
        if k not in t:
            errs.append("missing top-level key: %s" % k)
    if "pou" in t:
        for k in ("type", "name"):
            if k not in t["pou"]:
                errs.append("pou missing %s" % k)
    if "interface" in t:
        itf = t["interface"]
        for group in ("duts", "inputs", "outputs", "inouts"):
            for f in itf.get(group, []):
                if "name" not in f or "type" not in f:
                    errs.append("interface %s entry missing name/type" % group)
    for tc in t.get("test_cases", []):
        if "steps" not in tc or not tc["steps"]:
            errs.append("test_case %s has no steps" % tc.get("id"))
        for s in tc.get("steps", []):
            if "inputs" not in s or "expect" not in s:
                errs.append("test_case %s step missing inputs/expect"
                            % tc.get("id"))
    ref = t.get("reference", {})
    if not ref.get("pous"):
        errs.append("reference has no pous")
    return errs


def main():
    files = sorted(glob.glob(os.path.join(TASKS_DIR, "*.json")))
    if not files:
        print("no task files found in %s" % TASKS_DIR)
        return 1
    bad = 0
    for fn in files:
        t = json.load(open(fn, encoding="utf-8"))
        errs = check_task(t)
        if errs:
            bad += 1
        print("[%s] %-22s %s" % ("OK " if not errs else "ERR", t.get("id"),
                                  "; ".join(errs) if errs else ""))
    print("----\n%d file(s), %d with errors" % (len(files), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
