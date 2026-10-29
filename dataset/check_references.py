"""Compile-check every reference solution via the CODESYS compile service.

This is the dataset quality gate: a task whose reference solution does not
compile is unusable for the experiment. Run after building tasks.

Run:  python dataset/check_references.py
Exit: 0 all references compile, 1 compile failures, 2 tool/infra error.
"""
import json
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tool"))
from codesys_build import compile_jobs, CompileToolError  # noqa: E402


def main():
    files = sorted(glob.glob(os.path.join(HERE, "tasks", "*.json")))
    if not files:
        print("no task files found")
        return 2

    jobs = []
    for fn in files:
        t = json.load(open(fn, encoding="utf-8"))
        ref = t["reference"]
        jobs.append({
            "id": t["id"],
            "duts": ref.get("duts", []),
            "pous": ref["pous"],
            "auto_wire": ref.get("auto_wire", True),
        })

    try:
        report = compile_jobs(jobs)
    except CompileToolError as e:
        print("TOOL ERROR: %s" % e, file=sys.stderr)
        return 2

    n_fail = 0
    for r in report["results"]:
        if r.get("fatal"):
            n_fail += 1
            print("[FATAL] %-22s %s" % (r["id"], r["fatal"]))
        elif not r["passed"]:
            n_fail += 1
            print("[FAIL ] %-22s" % r["id"])
            for e in r["errors"]:
                print("        %s %s: %s"
                      % (e["code"], e.get("position_text") or "", e["text"]))
        else:
            print("[PASS ] %-22s" % r["id"])
    print("----\n%d reference(s), %d failed" % (len(report["results"]), n_fail))
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
