"""Render the dataset test cases as a template-aligned document.

For every task this script:

1. runs the task's reference implementation once in CODESYS simulation with
   per-step tracing (``codesys/simulate/runner.run_task(..., trace=True)``), so the document
   can show the *actual* output value of every scan step;
2. renders one block per test case in the layout required by the assignment's
   「测试用例模板与示例」: 名称 / 所属题目 / 初始状态 / 输入与步骤 / 预期输出 /
   覆盖内容 / 实际输出及结果, plus a per-step table whose last column is the
   step purpose (检查内容);
3. appends auto-derived coverage notes (inputs never driven, steps without any
   assertion, LTL specs not referenced by any case).

Usage:
    python dataset/render_cases.py                     # all tasks
    python dataset/render_cases.py --ids self_hard_002  # subset
    python dataset/render_cases.py --out report/测试用例.md
    python dataset/render_cases.py --no-run             # cached traces only

Traces are cached under ``dataset/.cache/tc_trace/`` (gitignored) because each
simulation takes tens of seconds.
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "codesys", "simulate"))

import driver  # noqa: E402
import runner  # noqa: E402

CACHE = os.path.join(HERE, ".cache", "tc_trace")
RESULTS_CSV = os.path.join(ROOT, "experiments", "results.csv")
DEFAULT_OUT = os.path.join(ROOT, "report", "测试用例.md")
PREFIXES = ("BOOL", "SINT", "INT", "DINT", "LINT", "USINT", "UINT", "UDINT",
            "ULINT", "BYTE", "WORD", "DWORD", "LWORD", "REAL", "LREAL", "TIME",
            "LTIME", "DATE", "DT", "TOD")


# --------------------------------------------------------------- formatting
def _fmt_bool(v):
    return "1" if v else "0"


def _fmt_input(v):
    if isinstance(v, bool):
        return _fmt_bool(v)
    if isinstance(v, float):
        return ("%g" % v)
    if isinstance(v, dict):
        return "{%s}" % ", ".join("%s=%s" % (k, _fmt_input(x))
                                  for k, x in v.items())
    if isinstance(v, list):
        return "[%s]" % ", ".join(_fmt_input(x) for x in v)
    if isinstance(v, str):
        return v
    return str(v)


def _split_raw(raw):
    """'WORD#32769' -> ('WORD', '32769'); 'TRUE' -> ('BOOL', 'TRUE')."""
    s = str(raw)
    if not s:
        return "", ""
    if "#" in s and not s.startswith("'") and not s.startswith('"'):
        head, tail = s.split("#", 1)
        return head.upper(), tail
    return "", s


def _fmt_actual(raw):
    """Readable form of a value read back from the PLC."""
    if raw is None:
        return "—"
    if str(raw).strip().upper() in ("TRUE", "FALSE"):
        return _fmt_bool(str(raw).strip().upper() == "TRUE")
    t, v = _split_raw(raw)
    if t == "BOOL":
        return "1" if v.upper() == "TRUE" else "0"
    if t in ("LTIME", "TIME"):
        ns = _time_ns(v)
        return _fmt_time(ns) if ns is not None else "T#" + v
    if t and t in PREFIXES:
        return v
    return v


_TIME_UNITS = {"d": 86400e9, "h": 3600e9, "m": 60e9, "s": 1e9,
               "ms": 1e6, "us": 1e3, "ns": 1.0}


def _time_ns(text):
    """'LTIME#1h2m3s4ms' -> nanoseconds (None if unparsable)."""
    s = str(text).strip()
    for p in ("LTIME#", "TIME#", "T#"):
        if s.upper().startswith(p):
            s = s[len(p):]
            break
    s = s.lower().replace(" ", "")
    if not s:
        return None
    total, num = 0.0, ""
    i = 0
    while i < len(s):
        ch = s[i]
        if ch.isdigit() or ch == ".":
            num += ch
            i += 1
            continue
        unit = None
        for u in ("ms", "us", "ns", "d", "h", "m", "s"):
            if s.startswith(u, i):
                unit = u
                break
        if unit is None or num == "":
            return None
        total += float(num) * _TIME_UNITS[unit]
        num = ""
        i += len(unit)
    return total if num == "" else None


def _fmt_time(ns):
    for unit in ("h", "m", "s", "ms", "us", "ns"):
        scale = _TIME_UNITS[unit]
        if ns >= scale:
            v = ns / scale
            return "T#%s%s" % ("%g" % v, unit)
    return "T#0ms"


def _same(expected, raw):
    """Compare an expected JSON value with the raw PLC value string."""
    if raw is None:
        return False
    t, v = _split_raw(raw)
    if isinstance(expected, bool):
        return v.upper() == ("TRUE" if expected else "FALSE")
    if isinstance(expected, str):
        if t in ("TIME", "LTIME") or expected.upper().startswith(("T#",
                                                                  "LTIME#")):
            a, b = _time_ns(expected), _time_ns(v)
            return a is not None and b is not None and abs(a - b) < 1.0
        if v[:1] in ("'", '"') and v[-1:] == v[:1]:
            v = v[1:-1]
        return v == expected
    if isinstance(expected, (int, float)):
        try:
            return abs(float(v) - float(expected)) <= \
                max(1e-6, abs(float(expected)) * 1e-9)
        except ValueError:
            return False
    return str(v) == str(expected)


# ------------------------------------------------------------- trace source
def _cache_path(tid):
    return os.path.join(CACHE, tid + ".json")


def _signature(task):
    """Cache key: traces depend only on the interface and the test vectors.

    Prose fields (``purpose``/``coverage``/``initialState``) are excluded, so
    editing wording does not invalidate the cached simulation results.
    """
    import hashlib
    cases = [{"id": c["id"], "scan_ms": c.get("scan_ms", 10),
              "steps": [{"inputs": s["inputs"], "expect": s["expect"],
                         "repeat": s.get("repeat", 1)} for s in c["steps"]]}
             for c in task["test_cases"]]
    payload = json.dumps({"interface": task["interface"], "cases": cases},
                         sort_keys=True, ensure_ascii=False)
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


def trace_task(task, force=False):
    """Return {'allPass', 'passCnt', 'failCnt', 'groups'} with traces."""
    path = _cache_path(task["id"])
    sig = _signature(task)
    if not force and os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            cached = json.load(f)
        if cached.get("_sig") == sig:
            return cached
    pous, duts = runner.reference_pous(task)
    if not pous:
        raise RuntimeError("%s: no reference POU" % task["id"])
    res = runner.run_task(task, pous, duts, trace=True)
    res["_sig"] = sig
    os.makedirs(CACHE, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    return res


def _case_actuals(task, res):
    """{case_id: [ {path: raw}, ... ]} with one entry per step."""
    by_id = {c["id"]: c for c in task["test_cases"]}
    out = {}
    for grp in res["groups"]:
        offset = 0
        for cid in grp["caseIds"]:
            n = len(by_id[cid]["steps"])
            steps = []
            for i in range(offset, offset + n):
                steps.append({p: vals[i] for p, vals in grp["trace"].items()})
            out[cid] = steps
            offset += n
    return out


def _model_results():
    """{task_id: [(label, tests_pass)]} from the experiment result table."""
    if not os.path.isfile(RESULTS_CSV):
        return {}
    import csv
    fw_name = {"self": "自研", "codex": "Codex"}
    out = {}
    with open(RESULTS_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            model = row["model"]
            short = "DeepSeek" if model.lower().startswith("deepseek") else (
                "Qwen" if model.lower().startswith("qwen") else model)
            label = "%s+%s" % (fw_name.get(row["framework"], row["framework"]),
                               short)
            ok = row.get("tests_pass") == "1"
            out.setdefault(row["task"], []).append((label, ok))
    for v in out.values():
        v.sort(key=lambda x: (0 if x[0].startswith("自研") else 1, x[0]))
    return out


# --------------------------------------------------------------- rendering
def _duts_map(task):
    return {d["name"]: {f["name"]: f["type"] for f in d.get("fields", [])}
            for d in task["interface"].get("duts", [])}


def _expect_leaves(task, key, val, duts):
    """Flatten one expect entry into [(path, expected, st_type)]."""
    struct_names = set(duts)
    itf = task["interface"]
    for e in itf["outputs"]:
        if e["name"] == key:
            tinfo = driver._classify(e["type"], struct_names)
            src = "fb[tc].%s" % key
            pre = "fb[tc]."
            break
    else:
        for e in itf["inouts"]:
            if e["name"] == key:
                tinfo = driver._classify(e["type"], struct_names)
                src = "io_%s[tc]" % key
                pre = "io_%s[tc]" % key
                break
        else:
            return []
    leaves = []
    for expr, st_type, ev in driver._leaf_pairs(src, val, tinfo, duts):
        path = _trace_path(expr)
        leaves.append((path, ev, st_type))
    return leaves


def _trace_path(expr):
    """Map a driver expression to the trace path used by driver.trace_specs."""
    if expr.startswith("fb[tc]."):
        return expr[len("fb[tc]."):]
    if expr.startswith("io_"):
        return expr.replace("io_", "", 1).replace("[tc]", "", 1)
    return expr


def _fmt_expect(leaves):
    if not leaves:
        return "—（本步不检查输出）"
    return "，".join("%s=%s" % (p, _fmt_input(v)) for p, v, _ in leaves)


def _step_actual_text(paths, actual):
    return "，".join("%s=%s" % (p, _fmt_actual(actual.get(p)))
                     for p in paths)


def _source_label(task):
    if task["id"].startswith("example"):
        return "schema 示例"
    return {"public": "公共题", "self_built": "自建题"}.get(
        task["source"], task["source"])


def _coverage_gaps(task):
    """Auto-derived hints: undriven BOOL inputs, unasserted steps, unused specs."""
    itf = task["interface"]
    driven = {i["name"]: set() for i in itf["inputs"]}
    empty_steps = []
    for c in task["test_cases"]:
        for i, st in enumerate(c["steps"]):
            for k, v in st["inputs"].items():
                if k in driven:
                    driven[k].add(bool(v))
            if not st["expect"]:
                empty_steps.append("%s 周期 %d" % (c["id"], i))
    undriven = [k for k, vs in driven.items() if True not in vs]
    used = {s for c in task["test_cases"] for s in c["specRefs"]}
    unused = [s["id"] for s in task["ltl_specs"] if s["id"] not in used]
    notes = []
    if undriven:
        notes.append("布尔输入从未被置为 TRUE（自 1）：%s" % "、".join(undriven))
    if empty_steps:
        notes.append("不含任何断言的扫描步：%s" % "、".join(empty_steps))
    if unused:
        notes.append("无用例关联的规约：%s" % "、".join(unused))
    return notes


def render_case(task, case, actuals, w):
    tid = task["id"]
    n_fail = 0
    rows = []
    paths = sorted(actuals[0].keys()) if actuals else []
    duts = _duts_map(task)
    for i, st in enumerate(case["steps"]):
        leaves = []
        for key, val in st["expect"].items():
            leaves += _expect_leaves(task, key, val, duts)
        actual = actuals[i] if i < len(actuals) else {}
        bad = [p for p, v, _ in leaves
               if not _same(v, actual.get(p))]
        if bad:
            n_fail += 1
        exp_txt = _fmt_expect(leaves)
        if bad:
            exp_txt += " ｜ **不一致**：%s" % "、".join(
                "%s（预期 %s，实际 %s）" % (
                    p,
                    _fmt_input(next(v for q, v, _ in leaves if q == p)),
                    _fmt_actual(actual.get(p))) for p in bad)
        cyc = str(i)
        rep = st.get("repeat", 1)
        if rep and rep > 1:
            cyc += "（连续 %d 拍）" % rep
        rows.append("| %s | %s | %s | %s | %s |" % (
            cyc,
            "，".join("%s=%s" % (k, _fmt_input(st["inputs"][k]))
                     for k in sorted(st["inputs"])),
            exp_txt,
            _step_actual_text(paths, actual),
            st["purpose"]))
    n_steps = len(case["steps"])
    result = ("✅ 通过（%d/%d 步断言一致）" % (n_steps - n_fail, n_steps)
              if not n_fail else "❌ 未通过（%d 步存在差异，见下表）" % n_fail)
    spec = "、".join(case["specRefs"])
    w("### %s %s\n" % (case["id"], case.get("description", "")))
    w("| 项目 | 内容 |")
    w("|---|---|")
    w("| 测试用例名称 | %s %s |" % (case["id"], case.get("description", "")))
    w("| 所属题目 | %s %s（%s，%s） |" % (
        tid, task["title"], task["difficulty"],
        _source_label(task)))
    w("| 初始状态 | %s |" % case["initialState"])
    w("| 输入与步骤 | 见下表，%d 个扫描周期；每步「设输入 → 执行一个扫描周期 → "
      "断言」 |" % n_steps)
    w("| 预期输出 | 见下表「预期输出」列（只比较列出的输出/元素，未列出的不做检查） |")
    w("| 覆盖内容 | %s |" % "；".join(case["coverage"]))
    w("| 关联规约 | %s（规约全文见报告附录 A） |" % spec)
    w("| 实际输出及结果 | %s；参考实现实测值见下表「实际输出」列 |" % result)
    w("")
    w("| 周期 | 输入 | 预期输出 | 实际输出 | 检查内容 |")
    w("|---|---|---|---|---|")
    for r in rows:
        w(r)
    w("")
    return n_fail


def render_task(task, res, w, model_results=None):
    actuals = _case_actuals(task, res)
    n_cases = len(task["test_cases"])
    n_steps = sum(len(c["steps"]) for c in task["test_cases"])
    w("## %s %s\n" % (task["id"], task["title"]))
    src = _source_label(task)
    w("- 难度：%s ｜ 来源：%s ｜ 被测 POU：`%s`（%s）" % (
        task["difficulty"], src,
        task["pou"]["name"], task["pou"]["type"]))
    scans = sorted({c.get("scan_ms", 10) for c in task["test_cases"]})
    w("- 测试规模：%d 组用例、%d 个扫描步；扫描周期 %s ms" % (
        n_cases, n_steps, "/".join(str(s) for s in scans)))
    hits = (model_results or {}).get(task["id"])
    if hits:
        w("- 四设置实测（测试通过）：%s（逐题指标见 `experiments/results.csv`）"
          % " ｜ ".join("%s %s" % (label, "✅" if ok else "❌")
                        for label, ok in hits))
    gaps = _coverage_gaps(task)
    if gaps:
        w("- 已知覆盖缺口（自动统计）：%s" % "；".join(gaps))
    w("- 数据集自检结果：参考实现 %s（%d/%d 步断言通过）\n" % (
        "全部通过" if res["allPass"] else "**未通过**",
        res["passCnt"], res["passCnt"] + res["failCnt"]))
    for case in task["test_cases"]:
        render_case(task, case, actuals.get(case["id"], []), w)


def main(argv):
    ids = None
    out = DEFAULT_OUT
    force = True
    if "--ids" in argv:
        i = argv.index("--ids")
        ids, argv = [], argv[:i] + argv[i + 1:]
        while argv and not argv[0].startswith("--"):
            ids.append(argv.pop(0))
    if "--out" in argv:
        out = argv[argv.index("--out") + 1]
    if "--no-run" in argv:
        force = False

    files = sorted(glob.glob(os.path.join(HERE, "tasks", "*.json")))
    diff_order = {"easy": 0, "medium": 1, "hard": 2}
    tasks, example = [], []
    for fn in files:
        t = json.load(open(fn, encoding="utf-8"))
        if ids and t["id"] not in ids:
            continue
        (example if t["id"].startswith("example") else tasks).append(t)
    tasks.sort(key=lambda t: (0 if t["source"] == "public" else 1,
                              diff_order.get(t["difficulty"], 9), t["id"]))
    if not tasks and not example:
        raise SystemExit("no task matched")

    lines = []

    def w(s=""):
        lines.append(s)

    total_steps = sum(sum(len(c["steps"]) for c in t["test_cases"])
                      for t in tasks)
    total_cases = sum(len(t["test_cases"]) for t in tasks)
    w("# 测试用例（按作业模板整理）\n")
    w("本节把 `dataset/tasks/*.json` 中的结构化用例渲染成作业文档"
      "「测试用例模板与示例」要求的格式：每个用例给出名称、所属题目、初始状态、"
      "输入与步骤、预期输出、覆盖内容、实际输出及结果，且**每一步都写明检查内容**。\n")
    w("| 覆盖范围 | 数量 |")
    w("|---|---|")
    w("| 题目 | %d（公共题 %d + 自建题 %d） |" % (
        len(tasks),
        sum(1 for t in tasks if t["source"] == "public"),
        sum(1 for t in tasks if t["source"] != "public")))
    w("| 测试用例 | %d 组 |" % total_cases)
    w("| 扫描步（测试步） | %d 个 |" % total_steps)
    w("")
    w("**执行与判定语义**\n")
    w("- 每个用例使用独立的被测功能块实例（内部状态从零开始），按下表顺序"
      "「设输入 → 执行一个扫描周期 → 断言输出」。")
    w("- 「周期」列为扫描步序号（从 0 开始）；标注「连续 N 拍」的步表示输入保持 "
      "N 个周期，在第 N 个周期结束后断言一次，用于让定时器/状态机推进。")
    w("- **只比较「预期输出」列列出的输出/元素**，未列出的输出不做检查；"
      "空表项记作「本步不检查输出」。")
    w("- 「实际输出」列由**参考实现在 CODESYS 仿真中逐拍实测**得到"
      "（`dataset/render_cases.py` 生成，缓存于 `dataset/.cache/`）。"
      "BOOLEAN 显示为 1/0，`T#` 为时间字面量。")
    w("- 模型生成代码的逐题判定结果（编译/测试通过率）见 `experiments/results.csv`"
      " 与实验报告第 5 章；自动测试会把同一套用例编译成 ST 自测驱动在 PLC 内执行，"
      "因此各框架、各模型使用完全相同的用例与判定标准。")
    w("")
    w("**用例目录**\n")
    for i, t in enumerate(tasks, 1):
        cases = "、".join("%s %s" % (c["id"], c.get("description", ""))
                         for c in t["test_cases"])
        w("%d. [%s %s](#%s) — %s" % (
            i, t["id"], t["title"], _slug(t["id"], t["title"]), cases))
    w("")

    model_results = _model_results()
    ok_all = True
    for i, t in enumerate(tasks, 1):
        try:
            res = trace_task(t, force=force)
        except Exception as e:      # keep rendering even if one task fails
            ok_all = False
            print("!! %s: %s" % (t["id"], e), file=sys.stderr)
            continue
        render_task(t, res, w, model_results)

    if example:
        w("---\n")
        w("## 附录：schema 示例（example_motor）\n")
        w("`dataset/tasks/example_motor.json` 是数据格式示例，不计入 30 道题，"
          "用于演示模板字段填法。\n")
        for t in example:
            try:
                res = trace_task(t, force=force)
            except Exception as e:
                ok_all = False
                print("!! %s: %s" % (t["id"], e), file=sys.stderr)
                continue
            render_task(t, res, w, model_results)

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("written -> %s (%d lines)" % (out, len(lines)))
    return 0 if ok_all else 1


def _slug(tid, title):
    return tid.lower().replace("_", "-") + "-" + _anchor(title)


def _anchor(text):
    """GitHub-style anchor slug for headings."""
    out = []
    for ch in text.lower():
        if ch.isalnum() or ch in "-_":
            out.append(ch)
    return "".join(out)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
