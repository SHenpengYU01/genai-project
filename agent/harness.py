"""Self-developed ST generation agent harness.

Loop: generate -> parse/validate -> (cheap) interface check -> compile via the
CODESYS compile service -> optional behavior tests in CODESYS simulation ->
structured feedback -> repair. Termination: success, max rounds, stalled
(identical code), or repeated identical failure signature.

CLI (offline demo with canned outputs):
    python -m agent.harness --task dataset/tasks/example_motor.json --mock
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "codesys", "compile"))
sys.path.insert(0, os.path.join(ROOT, "codesys", "simulate"))
sys.path.insert(0, ROOT)

from client import compile_jobs, CompileToolError  # noqa: E402
import runner  # noqa: E402
from agent import caller_gen, parser, prompt  # noqa: E402
from agent.llm import (LLMError, MockClient, OpenAICompatClient,  # noqa: E402
                       resolve_model)


def _fmt_val(v):
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, str):
        return v
    return json.dumps(v, ensure_ascii=False)


class Harness:
    def __init__(self, task, llm, max_rounds=5, use_tests=True,
                 compile_timeout=300.0, log=None):
        self.task = task
        self.llm = llm
        self.max_rounds = max_rounds
        self.use_tests = use_tests
        self.compile_timeout = compile_timeout
        self.log = log or (lambda *_: None)

    # -- message history trimming: system + task + last 2 exchanges --------
    def _trim(self, messages):
        if len(messages) > 6:
            del messages[2:len(messages) - 4]

    def _failures(self, tres):
        by_id = {c["id"]: c for c in self.task["test_cases"]}
        failures = []
        for g in tres["groups"]:
            tc = g.get("firstFailTc", -1)
            st = g.get("firstFailStep", -1)
            if tc is None or tc < 0 or not g.get("caseIds"):
                continue
            cid = g["caseIds"][tc]
            case = by_id.get(cid)
            if case is None:
                continue
            step = case["steps"][st] if st < len(case["steps"]) else {}
            mismatches = []
            for k, exp in (step.get("expect") or {}).items():
                act = g.get("failValues", {}).get(k, "<不可读>")
                mismatches.append((k, _fmt_val(exp), act))
            failures.append({"testCase": cid, "step": st,
                             "desc": case.get("description", ""),
                             "mismatches": mismatches})
        return failures

    def _compile(self, duts, pous):
        caller = caller_gen.generate(self.task)
        job = {"id": self.task["id"], "duts": duts,
               "pous": list(pous) + [caller], "auto_wire": False}
        report = compile_jobs([job], timeout=self.compile_timeout)
        return report["results"][0]

    @staticmethod
    def _dedupe(errors):
        seen, out = {}, []
        for e in errors:
            key = (e.get("code", ""), e.get("text", ""))
            if key in seen:
                seen[key]["count"] += 1
            else:
                rec = dict(e)
                rec["count"] = 1
                seen[key] = rec
                out.append(rec)
        return out

    def run(self):
        record = {
            "task": self.task["id"],
            "difficulty": self.task.get("difficulty"),
            "model": self.llm.name,
            "framework": getattr(self.llm, "framework", "agent"),
            "model_name": getattr(self.llm, "model_name", None),
            "use_tests": self.use_tests,
            "rounds": [],
            "status": None,
            "compiled": False,
            "compiled_first_try": None,
            "ever_compiled": False,
            "tests_passed": None,
        }
        messages = [{"role": "system", "content": prompt.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt.task_prompt(self.task)}]
        t0 = time.time()
        prev_code = None
        prev_sig = None
        same_sig = 0
        final_pous, final_duts = None, None

        for rnd in range(1, self.max_rounds + 1):
            self.log("round %d: calling model" % rnd)
            try:
                resp = self.llm.chat(messages)
            except LLMError as e:
                record["status"] = "llm_error"
                record["error"] = str(e)
                break

            text = resp["text"]
            rec = {"round": rnd, "usage": resp["usage"],
                   "finish_reason": resp.get("finish_reason"),
                   "llm_ms": resp.get("elapsed_ms", 0),
                   "raw_text": (text or "")[:8000]}
            record["rounds"].append(rec)

            parsed = parser.parse(text)
            rec["parse_errors"] = parsed["errors"]
            duts, pous = parsed["duts"], parsed["pous"]

            if not parsed["errors"] and any(p["name"] == "PLC_PRG"
                                            for p in pous):
                parsed["errors"].append(
                    "请勿输出名为 PLC_PRG 的程序（测试框架会创建调用者）")

            sig = None
            if parsed["errors"]:
                feedback = ("输出格式错误：\n- "
                            + "\n- ".join(parsed["errors"])
                            + "\n\n请按块格式重新输出完整代码。")
                if resp.get("finish_reason") == "length":
                    feedback += ("\n注意：本次输出因长度限制被截断，"
                                 "请精简实现并确保每个块以 <<<END>>> 结束。")
                sig = ("parse", tuple(parsed["errors"]))
            else:
                name_errs = (parser.check_duts(duts)
                             + parser.check_names(pous, duts))
                iface_errs = name_errs or parser.check_interface(self.task, pous)
                if iface_errs:
                    rec["interface_errors"] = iface_errs
                    feedback = prompt.interface_feedback(iface_errs)
                    sig = ("iface", tuple(sorted(iface_errs)))
                else:
                    try:
                        cres = self._compile(duts, pous)
                    except CompileToolError as e:
                        record["status"] = "tool_error"
                        record["error"] = str(e)
                        break
                    if cres.get("fatal"):
                        record["status"] = "tool_error"
                        record["error"] = cres["fatal"]
                        break
                    errors = self._dedupe(cres["errors"])
                    rec["compile"] = {"passed": cres["passed"],
                                      "errors": errors,
                                      "elapsed_ms": cres.get("elapsed_ms")}
                    if rnd == 1:
                        # first submission compiles? (format/interface
                        # failures in round 1 stay None -> recorded as False)
                        record["compiled_first_try"] = cres["passed"]
                    record["ever_compiled"] = (record["ever_compiled"]
                                               or cres["passed"])
                    record["compiled"] = cres["passed"]
                    final_pous, final_duts = pous, duts

                    if cres["passed"]:
                        if not self.use_tests:
                            record["status"] = "success"
                            record["tests_passed"] = None
                            break
                        try:
                            tres = runner.run_task(
                                self.task, pous, duts)
                        except Exception as e:  # simulation infra failure
                            record["status"] = "tool_error"
                            record["error"] = "test infra: %s" % e
                            break
                        failures = self._failures(tres)
                        rec["tests"] = {
                            "allPass": tres["allPass"],
                            "passCnt": tres["passCnt"],
                            "failCnt": tres["failCnt"],
                            "failures": failures,
                        }
                        record["tests_passed"] = tres["allPass"]
                        if tres["allPass"]:
                            record["status"] = "success"
                            break
                        feedback = prompt.test_feedback(rnd, failures)
                        sig = ("test", tuple((f["testCase"], f["step"])
                                             for f in failures))
                    else:
                        feedback = prompt.compile_feedback(rnd, errors)
                        sig = ("compile",
                               tuple((e.get("code"), e.get("text"))
                                     for e in errors))

            # termination heuristics -------------------------------------
            code_sig = tuple(
                (p["name"], p["declaration"], p["implementation"])
                for p in pous) + tuple((d["name"], d["declaration"])
                                       for d in duts)
            if prev_code == code_sig:
                rec["stopped"] = "stalled"
                record["status"] = "stalled"
                break
            prev_code = code_sig
            if sig is not None and sig == prev_sig:
                same_sig += 1
            else:
                same_sig = 0
            prev_sig = sig
            if same_sig >= 2:
                rec["stopped"] = "no_progress"
                record["status"] = "no_progress"
                break

            messages.append({"role": "assistant", "content": text})
            messages.append({"role": "user", "content": feedback})
            self._trim(messages)

        if record["status"] is None:
            record["status"] = "max_rounds"
        if record["compiled_first_try"] is None:
            record["compiled_first_try"] = False
        record["rounds_used"] = len(record["rounds"])
        record["wall_ms"] = int((time.time() - t0) * 1000)
        record["usage_total"] = dict(self.llm.total_usage)
        cost = self.llm.cost_usd()
        record["cost_usd"] = None if cost is None else round(cost, 6)
        if final_pous is not None:
            record["final_code"] = final_pous
            record["final_duts"] = final_duts
        record["success"] = record["status"] == "success"
        return record


def _mock_responses(task_path):
    root = os.path.dirname(task_path)
    mock_dir = os.path.join(ROOT, "experiments", "mocks", "reference")
    tid = json.load(open(task_path, encoding="utf-8"))["id"]
    path = os.path.join(mock_dir, tid + ".json")
    if not os.path.isfile(path):
        raise SystemExit("no mock for %s at %s" % (tid, path))
    return json.load(open(path, encoding="utf-8"))["responses"]


def make_llm(args, task_path):
    if args.mock:
        return MockClient(_mock_responses(task_path))
    if getattr(args, "framework", "agent") == "codex":
        from baseline.codex_client import CodexClient
        mid = args.model_name or resolve_model(args.model)["model"]
        return CodexClient(mid)
    return OpenAICompatClient(args.model, model_name=args.model_name)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--task", required=True)
    ap.add_argument("--model", default="deepseek")
    ap.add_argument("--framework", default="agent",
                    choices=("agent", "codex"),
                    help="agent = self harness; codex = Codex CLI baseline")
    ap.add_argument("--model-name", default=None,
                    help="exact provider model id (e.g. DeepSeek-V3.2); "
                         "default from DMXAPI_MODEL_<ALIAS> or built-in")
    ap.add_argument("--mock", action="store_true",
                    help="replay experiments/mocks/reference responses")
    ap.add_argument("--max-rounds", type=int, default=5)
    ap.add_argument("--no-tests", action="store_true")
    ap.add_argument("--out", default=None, help="write record JSON here")
    args = ap.parse_args()

    task = json.load(open(args.task, encoding="utf-8"))
    llm = make_llm(args, args.task)
    h = Harness(task, llm, max_rounds=args.max_rounds,
                use_tests=not args.no_tests,
                log=lambda m: print(m, file=sys.stderr))
    rec = h.run()
    text = json.dumps(rec, ensure_ascii=False, indent=1)
    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print("status=%s rounds=%d -> %s"
              % (rec["status"], rec["rounds_used"], args.out),
              file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
