"""探查：Codex 基线输出常缺 <<<IMPL>>> 标记时，解析器是否把函数体吞进声明区。

用法：python experiments/audit/reparse_probe.py [--compile] [--limit N]
把 codex_2models 记录里的 raw_text 用「容错解析」重新解析并（可选）重新编译，
对比与原记录一致的判定，量化「格式化差异」对基线成绩的影响。
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "codesys", "compile"))
sys.path.insert(0, os.path.join(ROOT, "codesys", "simulate"))

from agent import parser  # noqa: E402

POU_KIND_WORDS = ("FUNCTION_BLOCK", "PROGRAM", "FUNCTION")


def tolerant_parse(text):
    """Block parse that survives a missing <<<IMPL>>> marker and mis-tagged blocks.

    - POU block without <<<IMPL>>>: split the declaration text at its last
      leading END_VAR; everything after becomes the implementation.
    - A block tagged DUT whose body is really a POU: reclassify as POU.
    """
    duts, pous = [], []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = parser._OPEN.match(lines[i])
        if not m:
            i += 1
            continue
        tag, name, kind = m.group(1).upper(), m.group(2), m.group(3).lower()
        i += 1
        decl, impl, in_impl, closed = [], [], False, False
        while i < len(lines):
            if parser._IMPL.match(lines[i]):
                in_impl = True
                i += 1
                continue
            if parser._END.match(lines[i]):
                closed = True
                i += 1
                break
            (impl if in_impl else decl).append(lines[i])
            i += 1
        decl_txt = "\n".join(decl).strip()
        upper = decl_txt.upper()
        looks_pou = upper.startswith(POU_KIND_WORDS)
        if tag == "DUT" and (looks_pou or kind in ("function_block", "program",
                                                   "function")):
            tag = "POU"
        if tag == "DUT":
            if decl_txt:
                duts.append({"name": name, "kind": kind, "declaration": decl_txt})
            continue
        body = impl
        if not body:
            dl = decl_txt.splitlines()
            last = None
            for j, ln in enumerate(dl):
                if ln.strip().upper().startswith("END_VAR"):
                    last = j
            if last is not None and last < len(dl) - 1:
                decl_txt = "\n".join(dl[:last + 1]).strip()
                body = dl[last + 1:]
        if looks_pou:
            for w in POU_KIND_WORDS:
                if upper.startswith(w):
                    kind = {"FUNCTION_BLOCK": "function_block",
                            "PROGRAM": "program",
                            "FUNCTION": "function"}[w]
                    break
        pous.append({"name": name, "kind": kind or "function_block",
                     "declaration": decl_txt + "\n",
                     "implementation": ("\n".join(body).strip() + "\n")
                     if body else ""})
    return duts, pous


def load_rounds():
    out = []
    for f in sorted(glob.glob(os.path.join(
            ROOT, "experiments", "runs", "codex_2models", "tasks",
            "codex-qwen__*.json"))):
        rec = json.load(open(f, encoding="utf-8"))
        task = json.load(open(os.path.join(
            ROOT, "dataset", "tasks", rec["task"] + ".json"), encoding="utf-8"))
        out.append((rec, task))
    return out


def main(argv):
    do_compile = "--compile" in argv
    limit = None
    if "--limit" in argv:
        limit = int(argv[argv.index("--limit") + 1])

    pairs = load_rounds()
    jobs = []
    plan = []
    for rec, task in pairs:
        for rd in rec["rounds"]:
            txt = rd.get("raw_text") or ""
            if not txt:
                continue
            old_duts, old_pous = parser.parse(txt)["duts"], parser.parse(txt)["pous"]
            new_duts, new_pous = tolerant_parse(txt)
            old_impl = sum(len(p["implementation"]) for p in old_pous)
            new_impl = sum(len(p["implementation"]) for p in new_pous)
            gained = new_impl > old_impl + 20
            plan.append({"task": rec["task"], "round": rd["round"],
                         "gained": gained, "old_pous": old_pous,
                         "old_duts": old_duts, "new_pous": new_pous,
                         "new_duts": new_duts,
                         "old_compiled": (rd.get("compile") or {}).get("passed"),
                         "old_iface": rd.get("interface_errors") or []})
    gained = [p for p in plan if p["gained"]]
    print("rounds=%d, gained-implementation=%d" % (len(plan), len(gained)))
    if not do_compile:
        print("(未编译；加 --compile 对比重新编译结果)")
        return 0

    from agent import caller_gen
    from client import compile_jobs
    sel = gained if limit is None else gained[:limit]
    for p in sel:
        jobs.append({
            "id": "%s__r%d" % (p["task"], p["round"]),
            "auto_wire": False,
            "duts": p["new_duts"],
            "pous": p["new_pous"],
        })
    # caller POU per task
    taskmap = {rec["task"]: task for rec, task in pairs}
    for job in jobs:
        task = taskmap[job["id"].split("__r")[0]]
        job["pous"] = job["pous"] + [caller_gen.generate(task)]
    print("compiling %d jobs ..." % len(jobs))
    rep = compile_jobs(jobs)
    for r in rep["results"]:
        print("[%s] %-28s errors=%d %s"
              % ("PASS" if r["passed"] else "FAIL", r["id"], len(r["errors"]),
                 (r["errors"][0]["text"][:60] if r["errors"] else "")))
    n = len(rep["results"])
    ok = sum(1 for r in rep["results"] if r["passed"])
    print("----\n%d/%d 重新解析后可编译" % (ok, n))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
