"""行为测试执行器：用 CODESYS 仿真跑一题的测试用例（参考实现或模型生成的代码）。

用例按 scan_ms 分组，每组起一次 CODESYS 冷启动，用生成的 ST 自测驱动在 PLC 内
逐拍施加输入并断言输出。
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
RUN_BAT = os.path.join(HERE, "run_simulation.bat")
sys.path.insert(0, HERE)
import driver  # noqa: E402


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


def _scalar_keys(task):
    itf = task["interface"]
    struct_names = {d["name"] for d in itf.get("duts", [])}
    keys = []
    for grp in ("outputs", "inouts"):
        for e in itf.get(grp, []):
            if driver._classify(e["type"], struct_names)["kind"] == "scalar":
                keys.append(e["name"])
    return keys


def run_task(task, pous, duts=None, trace=False):
    """Run all test cases of `task` against `pous` (+ optional `duts`).

    `pous` must contain the function block under test (name == task['pou']['name']).
    With ``trace=True`` the driver also records the actual value of every
    output (and asserted inout) leaf at each step, read back per group as
    ``groups[i]['trace'] = {path: [value_str, ...]}`` in step order.
    Returns {"allPass", "passCnt", "failCnt", "groups": [...]}.
    """
    duts = duts or []
    cases = task["test_cases"]
    scalar_keys = _scalar_keys(task)

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
        driver_text = driver.generate(sub, trace=trace)
        n_steps = sum(len(c["steps"]) for c in groups[sm])
        specs = driver.trace_specs(sub) if trace else []
        if trace:
            reads = ["CI_TEST_DRIVER.%s[%d]" % (sp["var"], i)
                     for sp in specs for i in range(n_steps)]
        else:
            reads = ["CI_TEST_DRIVER.fail_%s" % k for k in scalar_keys]
        req = {"id": task["id"], "scan_ms": sm, "duts": duts,
               "pous": pous, "driver": driver_text,
               "debug_reads": reads}
        resp = _run_sim(req)
        if not resp.get("ok"):
            raise RuntimeError("simulation failed for scan_ms=%d: %s"
                               % (sm, resp.get("error")))
        total_pass += resp["passCnt"]
        total_fail += resp["failCnt"]
        all_pass = all_pass and resp["allPass"]
        fail_values = {}
        for k, v in (resp.get("debug") or {}).items():
            if not str(v).startswith("ERR"):
                fail_values[k.rsplit("fail_", 1)[-1]] = v
        grp = {
            "scan_ms": sm, "nCases": len(groups[sm]),
            "caseIds": [c["id"] for c in groups[sm]],
            "allPass": resp["allPass"], "passCnt": resp["passCnt"],
            "failCnt": resp["failCnt"],
            "firstFailTc": resp.get("firstFailTc"),
            "firstFailStep": resp.get("firstFailStep"),
            "failValues": fail_values,
        }
        if trace:
            debug = resp.get("debug") or {}
            grp["trace"] = {
                sp["path"]: [debug.get("CI_TEST_DRIVER.%s[%d]"
                                       % (sp["var"], i))
                             for i in range(n_steps)]
                for sp in specs}
        group_results.append(grp)

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
