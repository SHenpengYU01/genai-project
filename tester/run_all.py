"""Run every task's reference solution through the CODESYS-simulation tester.

This is the dataset self-check: it validates that each task's reference
implementation actually passes its own test cases (so the test cases and the
tester are correct before being used on model-generated code).

Run:  python tester/run_all.py [id_filter ...]
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run as runner  # noqa: E402

ROOT = os.path.dirname(HERE)
TASKS_DIR = os.path.join(ROOT, "dataset", "tasks")


def main():
    filters = sys.argv[1:]
    files = sorted(f for f in os.listdir(TASKS_DIR)
                   if f.endswith(".json") and f != "example_motor.json")
    results = []
    for f in files:
        task = json.load(open(os.path.join(TASKS_DIR, f), encoding="utf-8"))
        tid = task["id"]
        if filters and not any(x in tid for x in filters):
            continue
        t0 = time.time()
        try:
            r = runner.run_reference(task)
            status = "PASS" if r["allPass"] else "FAIL"
            detail = "pass=%d fail=%d" % (r["passCnt"], r["failCnt"])
        except Exception as e:
            status = "ERROR"
            detail = str(e).split("\n")[0][:180]
        dt = time.time() - t0
        results.append((tid, status, detail, dt))
        print("[%s] %-22s %s (%.1fs)"
              % (status, tid, detail, dt), flush=True)

    n_pass = sum(1 for _, s, _, _ in results if s == "PASS")
    n_fail = sum(1 for _, s, _, _ in results if s == "FAIL")
    n_err = sum(1 for _, s, _, _ in results if s == "ERROR")
    print("----")
    print("total=%d pass=%d fail=%d error=%d" % (len(results), n_pass, n_fail, n_err))
    for tid, s, d, _ in results:
        if s != "PASS":
            print("  %-22s %s %s" % (tid, s, d))


if __name__ == "__main__":
    main()
