"""Minimal example: a fix loop around the CODESYS compile service.

This is NOT the real generator agent - the LLM call is replaced by two canned
candidates. It shows exactly how a generator agent should consume the compile
feedback (error code + location + text) and decide when to stop.

Run:  python examples/agent_loop_example.py
Exit: 0 when the final candidate compiles, 1 otherwise.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from codesys_build import compile_st  # noqa: E402

TASK = {
    "name": "MotorCtrl",
    "kind": "function_block",
    "declaration": (
        "FUNCTION_BLOCK MotorCtrl\n"
        "VAR_INPUT\n    StartBtn : BOOL;\n    StopBtn : BOOL;\n    EStop : BOOL;\n"
        "END_VAR\nVAR_OUTPUT\n    Motor : BOOL;\nEND_VAR\n"),
}

# Candidate 1: forgets to declare nothing but references an undefined variable
# (a typical first-shot model mistake). Candidate 2 fixes it.
CANDIDATES = [
    "IF StopBtn OR EStop THEN\n    Motor := FALSE;\nELSIF StartBtn THEN\n"
    "    Motor := TRUE;\nEND_IF\nundeclared_var := 42;\n",
    "IF StopBtn OR EStop THEN\n    Motor := FALSE;\nELSIF StartBtn THEN\n"
    "    Motor := TRUE;\nEND_IF\n",
]

MAX_ATTEMPTS = len(CANDIDATES)


def llm_generate(task, previous_errors):
    """Replace with a real model call. previous_errors is the structured
    feedback list from the previous compile (empty on first attempt)."""
    idx = 1 if previous_errors else 0
    return CANDIDATES[idx]


def main():
    previous_errors = []
    for attempt in range(1, MAX_ATTEMPTS + 1):
        st = llm_generate(TASK, previous_errors)
        result = compile_st(
            name=TASK["name"],
            kind=TASK["kind"],
            declaration=TASK["declaration"],
            implementation=st,
            job_id="motor_attempt_%d" % attempt,
        )

        print("attempt %d -> %s (%.1fs)"
              % (attempt, "PASS" if result["passed"] else "FAIL",
                 result["elapsed_ms"] / 1000.0))

        if result.get("fatal"):
            print("infrastructure fatal error, cannot judge code:")
            print(result["fatal"])
            return 2

        if result["passed"]:
            print("compile accepted after %d attempt(s)" % attempt)
            return 0

        previous_errors = result["errors"]
        for e in previous_errors:
            # This is the exact feedback to serialise into the model prompt.
            print("  %s %s: %s"
                  % (e["code"], e.get("position_text") or "", e["text"]))

    print("exhausted %d attempts without a clean compile" % MAX_ATTEMPTS)
    return 1


if __name__ == "__main__":
    sys.exit(main())
