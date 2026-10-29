"""Run a task's test cases against a POU (reference or model code) via CODESYS
simulation.

Test cases are grouped by scan_ms; each group runs one simulation (one CODESYS
cold start) with that cycle time, using a generated self-test driver.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
RUN_BAT = os.path.join(HERE, "run_simulation.bat")
sys.path.insert(0, HERE)
import driver_gen  # noqa: E402


def _run_sim(request, timeout=600.0):
    workdir = os.path.join(HERE, "work")
    os.makedirs(workdir, exist_ok=True)
    fd, req = tempfile.mkstemp(prefix="req_", suffix=".json", dir=workdir)
    resp = req.replace("req_", "resp_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(request, f, ensure_ascii=False, indent=1)
        proc = subprocess.run(
            ["cmd", "/c", RUN_BAT, req, resp],
            cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=timeout)
        if not os.path.isfile(resp):
            raise RuntimeError(
                "no response file (exit=%s)\nSTDOUT:\n%s\nSTDERR:\n%s"
                % (proc.returncode,
                   proc.stdout.decode("gbk", "replace"),
                   proc.stderr.decode("gbk", "replace")))
        with open(resp, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    finally:
        for p in (req, resp):
            try:
                os.remove(p)
            except OSError:
                pass


def run_task(task, pous, duts=None):
    """Run all test cases of `task` against `pous` (+ optional `duts`).

    `pous` must contain the function block under test (name == task['pou']['name']).
    Returns {"allPass", "passCnt", "failCnt", "groups": [...]}.
    """
    duts = duts or []
    cases = task["test_cases"]

    groups = {}
    order = []
    for c in cases:
        sm = c.get("scan_ms", 10)
        if sm not in groups:
            groups[sm] = []
            order.append(sm)
        groups[sm].append(c)

    total_pass = 0
    total_fail = 0
    all_pass = True
    group_results = []
    for sm in order:
        sub = dict(task)
        sub["test_cases"] = groups[sm]
        driver = driver_gen.generate(sub)
        req = {"id": task["id"], "scan_ms": sm, "duts": duts,
               "pous": pous, "driver": driver}
        resp = _run_sim(req)
        if not resp.get("ok"):
            raise RuntimeError("simulation failed for scan_ms=%d: %s"
                               % (sm, resp.get("error")))
        total_pass += resp["passCnt"]
        total_fail += resp["failCnt"]
        all_pass = all_pass and resp["allPass"]
        group_results.append({
            "scan_ms": sm, "nCases": len(groups[sm]),
            "allPass": resp["allPass"], "passCnt": resp["passCnt"],
            "failCnt": resp["failCnt"],
            "firstFailTc": resp.get("firstFailTc"),
            "firstFailStep": resp.get("firstFailStep"),
        })

    return {"allPass": all_pass, "passCnt": total_pass,
            "failCnt": total_fail, "groups": group_results}


def reference_pous(task):
    """Extract the FB-under-test POU + duts from task['reference']."""
    ref = task.get("reference", {})
    fb_name = task["pou"]["name"]
    pous = [p for p in ref.get("pous", [])
            if p.get("name") == fb_name]
    return pous, ref.get("duts", [])


def run_reference(task):
    pous, duts = reference_pous(task)
    if not pous:
        raise RuntimeError("no reference POU named %s" % task["pou"]["name"])
    return run_task(task, pous, duts)


if __name__ == "__main__":
    root = os.path.dirname(HERE)
    path = os.path.join(root, "dataset", "tasks", sys.argv[1]
                        if len(sys.argv) > 1 else "example_motor.json")
    task = json.load(open(path, encoding="utf-8"))
    res = run_reference(task)
    print(json.dumps(res, ensure_ascii=False, indent=1))
