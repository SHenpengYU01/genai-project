"""Summarize an experiment run directory into markdown tables.

Usage: python experiments/summarize.py experiments/runs/agent_2models
"""
import glob
import json
import os
import sys


def load(outdir):
    runs = {}
    for f in sorted(glob.glob(os.path.join(outdir, "tasks", "*.json"))):
        r = json.load(open(f, encoding="utf-8"))
        fw = r.get("framework") or "agent"
        mn = r.get("model_name")
        if not mn:
            mn = r["model"].split("/", 1)[1] if "/" in r["model"] else r["model"]
        runs.setdefault("%s:%s" % (fw, mn), []).append(r)
    return runs


def pct(x):
    return "—" if x is None else "%.1f%%" % (x * 100)


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") \
        else "experiments/runs/agent_2models"
    out = None
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    if out:
        import io
        buf = io.StringIO()
        _main(outdir, buf)
        with open(out, "w", encoding="utf-8") as f:
            f.write(buf.getvalue())
        print("written -> %s" % out)
    else:
        _main(outdir, sys.stdout)


def _main(outdir, w):
    runs = load(outdir)
    if not runs:
        raise SystemExit("no records in %s" % outdir)

    def print(*a):
        w.write(" ".join(str(x) for x in a) + "\n")

    summary_path = os.path.join(outdir, "summary.json")
    if os.path.isfile(summary_path):
        cfg = json.load(open(summary_path, encoding="utf-8")).get("config", {})
        print("实验配置：模型 %s，任务 %s 道，max_rounds=%s，use_tests=%s\n"
              % (cfg.get("models"), cfg.get("task_count"),
                 cfg.get("max_rounds"), cfg.get("use_tests")))

    print("## 总体指标\n")
    print("| 模型 | 任务数 | 首次编译通过率 | 最终编译通过率 | 测试通过率 "
          "| 端到端成功率 | 平均轮次 | 平均耗时(s) | 输入tokens | 输出tokens |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for model, recs in runs.items():
        n = len(recs)
        def rate(p):
            return sum(1 for r in recs if p(r)) / n
        print("| %s | %d | %s | %s | %s | %s | %.2f | %.0f | %d | %d |"
              % (model, n,
                 pct(rate(lambda r: r.get("compiled_first_try"))),
                 pct(rate(lambda r: r.get("compiled"))),
                 pct(rate(lambda r: r.get("tests_passed") is True)),
                 pct(rate(lambda r: r.get("success"))),
                 sum(r["rounds_used"] for r in recs) / n,
                 sum(r["wall_ms"] for r in recs) / n / 1000.0,
                 sum(r["usage_total"]["prompt_tokens"] for r in recs),
                 sum(r["usage_total"]["completion_tokens"] for r in recs)))

    print("\n## 分难度\n")
    print("| 模型 | 难度 | n | 首次编译 | 最终编译 | 测试通过 | 成功率 | 平均轮次 |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- |")
    order = {"easy": 0, "medium": 1, "hard": 2}
    for model, recs in runs.items():
        groups = {}
        for r in recs:
            groups.setdefault(r.get("difficulty") or "?", []).append(r)
        for d in sorted(groups, key=lambda x: order.get(x, 9)):
            g = groups[d]
            n = len(g)
            def rate(p):
                return sum(1 for r in g if p(r)) / n
            print("| %s | %s | %d | %s | %s | %s | %s | %.2f |"
                  % (model, d, n,
                     pct(rate(lambda r: r.get("compiled_first_try"))),
                     pct(rate(lambda r: r.get("compiled"))),
                     pct(rate(lambda r: r.get("tests_passed") is True)),
                     pct(rate(lambda r: r.get("success"))),
                     sum(r["rounds_used"] for r in g) / n))

    print("\n## 未成功任务\n")
    print("| 模型 | 任务 | 难度 | 状态 | 轮次 | 卡点 |")
    print("| --- | --- | --- | --- | --- | --- |")
    for model, recs in runs.items():
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
            print("| %s | %s | %s | %s | %d | %s |"
                  % (model, r["task"], r.get("difficulty"), r["status"],
                     r["rounds_used"], stage))


if __name__ == "__main__":
    main()
