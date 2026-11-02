"""Summarize one or more experiment run directories into markdown tables.

Usage:
    python experiments/summarize.py experiments/runs/agent_2models
    python experiments/summarize.py experiments/runs/agent_2models \
        experiments/runs/codex_2models --out experiments/RESULTS_FULL.md
"""
import glob
import json
import os
import sys

FW_NAMES = {"agent": "自研 harness", "codex": "Codex CLI", "mock": "mock"}


def load_dirs(dirs):
    runs = {}
    for outdir in dirs:
        for f in sorted(glob.glob(os.path.join(outdir, "tasks", "*.json"))):
            r = json.load(open(f, encoding="utf-8"))
            fw = r.get("framework") or "agent"
            mn = r.get("model_name")
            if not mn:
                mn = r["model"].split("/", 1)[1] if "/" in r["model"] \
                    else r["model"]
            runs.setdefault((fw, mn), []).append(r)
    return runs


def pct(x):
    return "—" if x is None else "%.1f%%" % (x * 100)


def agg(recs):
    n = len(recs)
    def rate(p):
        return sum(1 for r in recs if p(r)) / n
    return {
        "n": n,
        "first": rate(lambda r: r.get("compiled_first_try")),
        "final": rate(lambda r: r.get("compiled")),
        "tests": rate(lambda r: r.get("tests_passed") is True),
        "success": rate(lambda r: r.get("success")),
        "rounds": sum(r["rounds_used"] for r in recs) / n,
        "wall": sum(r["wall_ms"] for r in recs) / n / 1000.0,
        "tin": sum(r["usage_total"]["prompt_tokens"] for r in recs),
        "tout": sum(r["usage_total"]["completion_tokens"] for r in recs),
    }


def main():
    argv = sys.argv[1:]
    out = None
    if "--out" in argv:
        i = argv.index("--out")
        out = argv[i + 1]
        del argv[i:i + 2]
    dirs = [a for a in argv if not a.startswith("-")] or \
        ["experiments/runs/agent_2models"]
    if out:
        import io
        buf = io.StringIO()
        _main(dirs, buf)
        with open(out, "w", encoding="utf-8") as f:
            f.write(buf.getvalue())
        print("written -> %s" % out)
    else:
        _main(dirs, sys.stdout)


def _main(dirs, w):
    runs = load_dirs(dirs)
    if not runs:
        raise SystemExit("no records in %s" % ", ".join(dirs))

    def print(*a):
        w.write(" ".join(str(x) for x in a) + "\n")

    print("数据来源：%s\n" % ", ".join(dirs))
    print("## 总体指标\n")
    print("| 框架 | 模型 | 任务数 | 首次编译 | 最终编译 | 测试通过 "
          "| 端到端成功 | 平均轮次 | 平均耗时(s) | 输入tokens | 输出tokens |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for (fw, mn), recs in runs.items():
        a = agg(recs)
        print("| %s | %s | %d | %s | %s | %s | %s | %.2f | %.0f | %d | %d |"
              % (FW_NAMES.get(fw, fw), mn, a["n"], pct(a["first"]),
                 pct(a["final"]), pct(a["tests"]), pct(a["success"]),
                 a["rounds"], a["wall"], a["tin"], a["tout"]))

    # 2x2 matrix: framework x model (first compile / tests pass)
    fws = []
    models = []
    for fw, mn in runs:
        if fw not in fws:
            fws.append(fw)
        if mn not in models:
            models.append(mn)
    if len(fws) > 1 and len(models) > 1:
        print("\n## 实验设置矩阵（首次编译通过率 / 测试通过率）\n")
        print("| 框架 | " + " | ".join(models) + " |")
        print("| --- | " + " | ".join("---" for _ in models) + " |")
        for fw in fws:
            cells = []
            for mn in models:
                recs = runs.get((fw, mn))
                if not recs:
                    cells.append("—")
                else:
                    a = agg(recs)
                    cells.append("%s / %s" % (pct(a["first"]), pct(a["tests"])))
            print("| %s | %s |" % (FW_NAMES.get(fw, fw), " | ".join(cells)))

    print("\n## 分难度（测试通过率）\n")
    hdr = "| 框架 | 模型 | " + " | ".join(
        ["easy", "medium", "hard"]) + " |"
    print(hdr)
    print("| --- | --- | --- | --- | --- |")
    order = {"easy": 0, "medium": 1, "hard": 2}
    for (fw, mn), recs in runs.items():
        groups = {}
        for r in recs:
            groups.setdefault(r.get("difficulty") or "?", []).append(r)
        cells = []
        for d in ("easy", "medium", "hard"):
            g = groups.get(d)
            cells.append("—" if not g else
                         pct(sum(1 for r in g if r.get("tests_passed") is True)
                             / len(g)))
        print("| %s | %s | %s |" % (FW_NAMES.get(fw, fw), mn,
                                    " | ".join(cells)))

    print("\n## 未成功任务\n")
    print("| 框架 | 模型 | 任务 | 难度 | 状态 | 轮次 | 卡点 |")
    print("| --- | --- | --- | --- | --- | --- | --- |")
    for (fw, mn), recs in runs.items():
        for r in recs:
            if r.get("success"):
                continue
            if r.get("status") == "tool_error":
                stage = "工具错误"
            elif not r.get("compiled"):
                stage = "编译未通过"
            elif not r.get("tests_passed"):
                stage = "测试未通过"
            else:
                stage = "—"
            print("| %s | %s | %s | %s | %s | %d | %s |"
                  % (FW_NAMES.get(fw, fw), mn, r["task"],
                     r.get("difficulty"), r["status"], r["rounds_used"],
                     stage))


if __name__ == "__main__":
    main()
