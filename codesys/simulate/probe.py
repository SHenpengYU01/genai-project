"""单题调试：跑一题（第一组用例），并读回任意符号的实测值。

Usage: python codesys/simulate/probe.py <task.json> <symbol1,symbol2,...>
Symbols are read after the driver finishes, e.g.
CI_TEST_DRIVER.fb[0].ipValue
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import driver  # noqa: E402
import runner  # noqa: E402


def main():
    root = os.path.dirname(os.path.dirname(HERE))
    task = json.load(open(os.path.join(root, "dataset", "tasks", sys.argv[1]),
                           encoding="utf-8"))
    symbols = sys.argv[2].split(",") if len(sys.argv) > 2 else []
    fb = task["pou"]["name"]
    duts = task.get("reference", {}).get("duts", [])
    pous = [p for p in task.get("reference", {}).get("pous", [])
            if p["name"] == fb]

    # run only the first test case group
    cases = task["test_cases"]
    sm = cases[0].get("scan_ms", 10)
    sub = dict(task)
    sub["test_cases"] = [c for c in cases if c.get("scan_ms", 10) == sm]
    driver_text = driver.generate(sub)
    req = {"id": task["id"], "scan_ms": sm, "duts": duts, "pous": pous,
           "driver": driver_text, "debug_reads": symbols}
    resp = runner._run_sim(req)
    print(json.dumps(resp, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
