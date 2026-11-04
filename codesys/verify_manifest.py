"""CODESYS 服务一致性校验：重构/改动前后生成同一份清单并 diff。

输出写到 codesys/work/_verify/（已 gitignore）。

它把 CODESYS 服务的全部可观测产物打成一份带标签的清单，改动前后各生成一次后
直接 diff：清单相同即说明"编译诊断、驱动文本、参考实现编译、仿真逐拍结果"都没有变化。

Sections:
  drivers    - driver text for every task, default and trace=True (sha1)
  compile    - examples/batch_all.json per-job (passed, error codes/texts)
  dut        - examples/test_dut.py expectations
  references - dataset/check_references.py per-task compile outcome
  simulate   - per-task (allPass, passCnt, failCnt, trace digest)

Usage:
  python codesys/verify_manifest.py make --label before [--skip-simulate] [--sim-from-cache]
  python codesys/verify_manifest.py make --label after  [--skip-simulate]
  python codesys/verify_manifest.py diff before after
"""
import glob
import hashlib
import json
import os
import subprocess
import sys


def _find_root(start):
    d = start
    while True:
        if os.path.isdir(os.path.join(d, "dataset", "tasks")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            raise SystemExit("repo root not found from %s" % start)
        d = parent


ROOT = _find_root(os.path.dirname(os.path.abspath(__file__)))
TASKS = os.path.join(ROOT, "dataset", "tasks")
CACHE = os.path.join(ROOT, "dataset", ".cache", "tc_trace")


def _layout():
    """Locate the CODESYS service modules; supports the pre-refactor layout.

    new: codesys/{compile,simulate}/   old: tool/ + tester/
    The old layout is needed to record a baseline from a worktree checked out
    at an earlier commit.
    """
    new = {"driver": ("codesys", "simulate", "driver.py"),
           "runner": ("codesys", "simulate"),
           "compile": ("codesys", "compile"),
           "examples": ("codesys", "compile", "examples"),
           "work": ("codesys", "work", "_verify")}
    old = {"driver": ("tester", "driver_gen.py"),
           "runner": ("tester",),
           "compile": ("tool",),
           "examples": ("tool", "examples"),
           "work": ("codesys", "work", "_verify")}
    for cand in (new, old):
        if os.path.isfile(os.path.join(ROOT, *cand["driver"])):
            return cand
    raise SystemExit("CODESYS service modules not found under %s" % ROOT)


LAYOUT = _layout()
OUT = os.path.join(ROOT, *LAYOUT["work"])


def _sha(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def load_tasks():
    out = []
    for fn in sorted(glob.glob(os.path.join(TASKS, "*.json"))):
        out.append(json.load(open(fn, encoding="utf-8")))
    return out


def drivers_section():
    import importlib.util
    path = os.path.join(ROOT, *LAYOUT["driver"])
    spec = importlib.util.spec_from_file_location("driver", path)
    dg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dg)
    sec = {}
    for t in load_tasks():
        sec[t["id"]] = {"plain": _sha(dg.generate(t)),
                        "trace": _sha(dg.generate(t, trace=True)),
                        "trace_leaves": [s["path"] for s in dg.trace_specs(t)]}
    return sec


def compile_section():
    sys.path.insert(0, os.path.join(ROOT, *LAYOUT["compile"]))
    try:
        from client import compile_jobs          # new layout
    except ImportError:
        from codesys_build import compile_jobs   # pre-refactor layout
    req = json.load(open(os.path.join(ROOT, *(LAYOUT["examples"] + (
        "batch_all.json",))), encoding="utf-8"))
    rep = compile_jobs(req["jobs"])
    out = {}
    for r in rep["results"]:
        out[r["id"]] = {
            "passed": r["passed"],
            "fatal": r["fatal"],
            "errors": sorted("%s|%s" % (e.get("code") or "", e.get("text"))
                             for e in r["errors"]),
            "wire": sorted(r.get("wire_warnings") or []),
        }
    return out


def dut_section():
    sys.path.insert(0, os.path.join(ROOT, *LAYOUT["compile"]))
    sys.path.insert(0, os.path.join(ROOT, *LAYOUT["examples"]))
    import test_dut
    try:
        from client import compile_jobs
    except ImportError:
        from codesys_build import compile_jobs
    rep = compile_jobs(test_dut.JOBS)
    out = {}
    for r in rep["results"]:
        out[r["id"]] = {"passed": r["passed"],
                        "expected": test_dut.EXPECTED_PASSED[r["id"]],
                        "n_errors": len(r["errors"])}
    return out


def references_section():
    env = dict(os.environ)
    proc = subprocess.run([sys.executable,
                           os.path.join(ROOT, "dataset", "check_references.py")],
                          cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, env=env, timeout=1800)
    text = proc.stdout.decode("utf-8", "replace")
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("["):
            continue
        try:
            status = line[1:line.index("]")]
        except ValueError:
            continue
        rest = line[line.index("]") + 1:].strip().split()
        if not rest:
            continue
        out[rest[0]] = status
    return {"exit": proc.returncode, "tasks": out}


def simulate_section_from_cache():
    out = {}
    for fn in sorted(glob.glob(os.path.join(CACHE, "*.json"))):
        d = json.load(open(fn, encoding="utf-8"))
        digest = {p: _sha(json.dumps(v, ensure_ascii=False))
                  for p, v in sorted((g.get("trace") or {}).items() for g in d["groups"])[0][1].items()} \
            if False else None
        traces = {}
        for g in d["groups"]:
            for p, vals in (g.get("trace") or {}).items():
                traces["%s@%s" % (p, g["scan_ms"])] = _sha(
                    json.dumps(vals, ensure_ascii=False))
        out[os.path.basename(fn)[:-len(".json")]] = {
            "allPass": d["allPass"], "passCnt": d["passCnt"],
            "failCnt": d["failCnt"], "trace": traces,
        }
    return out


def simulate_section(live=True):
    sys.path.insert(0, os.path.join(ROOT, *LAYOUT["runner"]))
    try:
        import runner                         # new layout
    except ImportError:
        import run as runner                  # pre-refactor layout
    out = {}
    for t in load_tasks():
        pous, duts = runner.reference_pous(t)
        res = runner.run_task(t, pous, duts, trace=True)
        traces = {}
        for g in res["groups"]:
            for p, vals in (g.get("trace") or {}).items():
                traces["%s@%s" % (p, g["scan_ms"])] = _sha(
                    json.dumps(vals, ensure_ascii=False))
        out[t["id"]] = {"allPass": res["allPass"], "passCnt": res["passCnt"],
                        "failCnt": res["failCnt"], "trace": traces}
        print("  sim %-22s allPass=%s pass=%d" % (t["id"], res["allPass"],
                                                  res["passCnt"]), flush=True)
    return out


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    cmd = argv[0]
    if cmd == "make":
        label = argv[argv.index("--label") + 1] if "--label" in argv else "run"
        skip_sim = "--skip-simulate" in argv
        from_cache = "--sim-from-cache" in argv
        man = {}
        print("[1/5] drivers", flush=True)
        man["drivers"] = drivers_section()
        print("[2/5] compile examples", flush=True)
        man["compile"] = compile_section()
        print("[3/5] dut examples", flush=True)
        man["dut"] = dut_section()
        print("[4/5] reference compile", flush=True)
        man["references"] = references_section()
        if skip_sim:
            man["simulate"] = None
        elif from_cache:
            print("[5/5] simulate (from cache)", flush=True)
            man["simulate"] = simulate_section_from_cache()
        else:
            print("[5/5] simulate (live, slow)", flush=True)
            man["simulate"] = simulate_section()
        os.makedirs(OUT, exist_ok=True)
        path = os.path.join(OUT, "%s.json" % label)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(man, f, ensure_ascii=False, indent=1, sort_keys=True)
        print("written -> %s" % path)
        return 0

    if cmd == "diff":
        a = json.load(open(os.path.join(OUT, "%s.json" % argv[1]),
                           encoding="utf-8"))
        b = json.load(open(os.path.join(OUT, "%s.json" % argv[2]),
                           encoding="utf-8"))
        bad = 0
        for key in sorted(a):
            if a[key] == b[key]:
                print("SAME  %s" % key)
                continue
            if a[key] is None or b[key] is None:
                print("SKIP  %s (one side omitted)" % key)
                continue
            bad += 1
            print("DIFF  %s" % key)
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                for k in sorted(set(a[key]) | set(b[key])):
                    if a[key].get(k) != b[key].get(k):
                        print("   %s:\n     before=%s\n     after =%s"
                              % (k, json.dumps(a[key].get(k),
                                               ensure_ascii=False)[:400],
                                 json.dumps(b[key].get(k),
                                            ensure_ascii=False)[:400]))
        print("----\n%d section(s) differ" % bad)
        return 0 if bad == 0 else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
