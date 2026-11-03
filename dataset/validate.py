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

# 测试用例模板（作业文档「测试用例模板与示例」）要求的用例级/步级字段
REQUIRED_CASE = ["initialState", "coverage", "specRefs"]
REQUIRED_STEP = ["inputs", "expect", "purpose"]


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
        for f in itf.get("duts", []):
            if "name" not in f or "kind" not in f:
                errs.append("interface duts entry missing name/kind")
        for group in ("inputs", "outputs", "inouts"):
            for f in itf.get(group, []):
                if "name" not in f or "type" not in f:
                    errs.append("interface %s entry missing name/type" % group)
    spec_ids = {s.get("id") for s in t.get("ltl_specs", [])}
    for tc in t.get("test_cases", []):
        cid = tc.get("id")
        if "steps" not in tc or not tc["steps"]:
            errs.append("test_case %s has no steps" % cid)
        for k in REQUIRED_CASE:
            if k not in tc:
                errs.append("test_case %s missing %s" % (cid, k))
        for k in ("initialState",):
            if not str(tc.get(k, "")).strip():
                errs.append("test_case %s has empty %s" % (cid, k))
        cov = tc.get("coverage") or []
        if not cov or not all(str(c).strip() for c in cov):
            errs.append("test_case %s coverage must be non-empty strings" % cid)
        refs = tc.get("specRefs") or []
        unknown = [r for r in refs if r not in spec_ids]
        if not refs or unknown:
            errs.append("test_case %s specRefs empty or unknown: %s"
                        % (cid, unknown))
        for i, s in enumerate(tc.get("steps", [])):
            for k in REQUIRED_STEP:
                if k not in s:
                    errs.append("test_case %s step %d missing %s" % (cid, i, k))
            if not str(s.get("purpose", "")).strip():
                errs.append("test_case %s step %d has empty purpose" % (cid, i))
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
