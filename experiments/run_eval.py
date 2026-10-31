"""Experiment runner: tasks x models x (optional) frameworks.

Example (offline self-test with reference mocks):
    python experiments/run_eval.py --mock reference --outdir experiments/runs/mock_ref

Real runs (needs API keys in env):
    python experiments/run_eval.py --models deepseek,qwen --outdir experiments/runs/agent_2models
    python experiments/run_eval.py --models deepseek --limit 3 --outdir experiments/runs/deepseek_quick
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from agent.harness import Harness  # noqa: E402
from agent.llm import MockClient, OpenAICompatClient  # noqa: E402

TASKS_DIR = os.path.join(ROOT, "dataset", "tasks")


def load_tasks(sel, limit=None):
    files = sorted(f for f in os.listdir(TASKS_DIR)
                   if f.endswith(".json") and f != "example_motor.json")
    tasks = []
    for f in files:
        t = json.load(open(os.path.join(TASKS_DIR, f), encoding="utf-8"))
        if sel and not any(s in t["id"] for s in sel):
            continue
        tasks.append(t)
    if limit:
        tasks = tasks[:limit]
    return tasks


def mock_responses(task, variant):
    path = os.path.join(HERE, "mocks", variant, task["id"] + ".json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)["responses"]


def aggregate(records):
    n = len(records)
    if n == 0:
        return {}
    def rate(pred):
        return round(sum(1 for r in records if pred(r)) / n, 4)
    status = {}
    for r in records:
        status[r["status"]] = status.get(r["status"], 0) + 1
    costs = [r["cost_usd"] for r in records
             if r.get("cost_usd") is not None]
    return {
        "n_tasks": n,
        "compile_first_try_rate": rate(lambda r: bool(r.get("compiled_first_try"))),
        "compile_final_rate": rate(lambda r: bool(r.get("compiled"))),
        "tests_all_pass_rate": (rate(lambda r: bool(r.get("tests_passed")))
                                if records[0].get("use_tests") else None),
        "success_rate": rate(lambda r: r["success"]),
        "status_counts": status,
        "avg_rounds": round(sum(r["rounds_used"] for r in records) / n, 2),
        "avg_wall_s": round(sum(r["wall_ms"] for r in records) / n / 1000.0, 1),
        "tokens_in": sum(r["usage_total"]["prompt_tokens"] for r in records),
        "tokens_out": sum(r["usage_total"]["completion_tokens"] for r in records),
        "cost": (round(sum(costs), 4) if costs else None),
        "cost_unit": "provider billing currency (未配置价格时为 null)",
    }


def by_group(records, key, getter):
    groups = {}
    for r in records:
        groups.setdefault(getter(r), []).append(r)
    return {k: aggregate(v) for k, v in sorted(groups.items())}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--models", default="deepseek",
                    help="comma-separated aliases (deepseek,qwen)")
    ap.add_argument("--model-names", default="",
                    help="exact provider model ids per alias, e.g. "
                         "deepseek=DeepSeek-V3.2,qwen=qwen3-max")
    ap.add_argument("--mock", default=None,
                    help="replay scripted outputs from mocks/<variant>/ "
                         "(reference | broken_once | test_fail_once | ...)")
    ap.add_argument("--tasks", default="", help="comma-separated id substrings")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--max-rounds", type=int, default=5)
    ap.add_argument("--no-tests", action="store_true")
    ap.add_argument("--resume", action="store_true",
                    help="reuse existing per-task records (skip tool_error runs)")
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    sel = [s for s in args.tasks.split(",") if s]
    tasks = load_tasks(sel, args.limit)
    if not tasks:
        raise SystemExit("no tasks selected")
    models = ["mock-%s" % args.mock] if args.mock else \
        [m.strip() for m in args.models.split(",") if m.strip()]
    model_names = {}
    for part in args.model_names.split(","):
        if "=" in part:
            alias, _, name = part.partition("=")
            model_names[alias.strip()] = name.strip()

    os.makedirs(os.path.join(args.outdir, "tasks"), exist_ok=True)
    summary = {"runs": {}, "started": time.strftime("%Y-%m-%d %H:%M:%S"),
               "config": {
                   "models": models,
                   "model_names": model_names,
                   "mock": args.mock,
                   "max_rounds": args.max_rounds,
                   "use_tests": not args.no_tests,
                   "resume": args.resume,
                   "tasks": [t["id"] for t in tasks],
                   "task_count": len(tasks),
               }}
    for model in models:
        records = []
        print("== model %s ==" % model, flush=True)
        for task in tasks:
            fn = os.path.join(args.outdir, "tasks",
                              "%s__%s.json" % (model.replace("/", "_"),
                                               task["id"]))
            if args.resume and os.path.isfile(fn):
                try:
                    with open(fn, encoding="utf-8") as f:
                        rec = json.load(f)
                    if rec.get("status") != "tool_error":
                        records.append(rec)
                        print("  [%-11s] %-22s rounds=%d (resumed)"
                              % (rec["status"], task["id"],
                                 rec["rounds_used"]), flush=True)
                        continue
                except Exception:
                    pass
            if args.mock:
                llm = MockClient(mock_responses(task, args.mock))
            else:
                llm = OpenAICompatClient(
                    model, model_name=model_names.get(model))
            h = Harness(task, llm, max_rounds=args.max_rounds,
                        use_tests=not args.no_tests)
            t0 = time.time()
            rec = h.run()
            records.append(rec)
            with open(fn, "w", encoding="utf-8") as f:
                json.dump(rec, f, ensure_ascii=False, indent=1)
            print("  [%-11s] %-22s rounds=%d wall=%.0fs%s"
                  % (rec["status"], task["id"], rec["rounds_used"],
                     time.time() - t0,
                     "" if not rec.get("error") else "  ERR:" + rec["error"][:80]),
                  flush=True)
        name = model_names.get(model)
        if not name and records:
            nm = records[0].get("model") or ""
            name = nm.split("/", 1)[1] if "/" in nm else None
        summary["runs"][model] = {
            "model_name": name,
            "overall": aggregate(records),
            "by_difficulty": by_group(records, "difficulty",
                                      lambda r: r.get("difficulty") or "?"),
        }
        with open(os.path.join(args.outdir, "summary.json"), "w",
                  encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=1)

    print("\n== summary ==")
    for model, s in summary["runs"].items():
        o = s["overall"]
        print("%s (%s): n=%d first_compile=%.2f final_compile=%.2f "
              "tests_pass=%s success=%.2f avg_rounds=%.2f cost=%s"
              % (model, s.get("model_name") or "-", o["n_tasks"],
                 o["compile_first_try_rate"], o["compile_final_rate"],
                 "-" if o["tests_all_pass_rate"] is None
                 else "%.2f" % o["tests_all_pass_rate"],
                 o["success_rate"], o["avg_rounds"],
                 "n/a" if o["cost"] is None else "%.4f" % o["cost"]))
    print("written -> %s" % os.path.join(args.outdir, "summary.json"))


if __name__ == "__main__":
    main()
