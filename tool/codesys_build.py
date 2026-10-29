"""Python client for the CODESYS ST compile service.

Two usage modes
---------------

1. Library (recommended for agent harnesses):

    from codesys_build import compile_st, compile_jobs

    r = compile_st(
        name="MotorCtrl",
        kind="function_block",
        declaration="FUNCTION_BLOCK MotorCtrl\\nVAR_INPUT ...",
        implementation="...",
    )
    if r["passed"]:
        ...
    else:
        for e in r["errors"]:
            print(e["code"], e["position_text"], e["text"])

    # many POUs / many tasks in ONE CODESYS cold start (~30-40s once):
    report = compile_jobs([job1, job2, ...])

2. Command line:

    python codesys_build.py request.json [response.json]
    echo %ERRORLEVEL%    # 0 all passed, 1 build failures, 2 tool/infra error

The service launches CODESYS.exe --noUI once per batch; put as many jobs as
possible into one call to amortise the cold-start cost.

Response shape (per result)::

    {
      "id": "...", "passed": bool, "fatal": str|None, "elapsed_ms": int,
      "errors":   [{"severity","category","text","code","position_text",
                    "position","length"}],
      "warnings": [ ... same fields ... ],
      "info_count": int, "wire_warnings": [str], "project_copy": str|None
    }
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
RUN_BAT = os.path.join(HERE, "run_compile.bat")

# Exit codes produced by this client / batch runner.
EXIT_ALL_PASSED = 0
EXIT_BUILD_FAILED = 1
EXIT_TOOL_ERROR = 2


class CompileToolError(RuntimeError):
    """Infrastructure problem (CODESYS missing, timeout, worker crash)."""


def _run_batch(request: dict, timeout: float = 300.0) -> dict:
    if not os.path.isfile(RUN_BAT):
        raise CompileToolError("runner not found: %s" % RUN_BAT)
    workdir = os.path.join(HERE, "work")
    os.makedirs(workdir, exist_ok=True)
    fd, req_path = tempfile.mkstemp(prefix="req_", suffix=".json", dir=workdir)
    resp_path = req_path.replace("req_", "resp_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(request, f, ensure_ascii=False, indent=1)
        t0 = time.time()
        proc = subprocess.run(
            ["cmd", "/c", RUN_BAT, req_path, resp_path],
            cwd=HERE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        wall = time.time() - t0
        if not os.path.isfile(resp_path):
            raise CompileToolError(
                "no response file (%.1fs, exit=%s)\nSTDOUT:\n%s\nSTDERR:\n%s"
                % (wall, proc.returncode,
                   proc.stdout.decode("gbk", "replace"),
                   proc.stderr.decode("gbk", "replace")))
        with open(resp_path, "r", encoding="utf-8-sig") as f:
            report = json.load(f)
        if not report.get("ok"):
            raise CompileToolError("worker fatal error:\n%s"
                                   % report.get("error"))
        report["client_elapsed_ms"] = int(wall * 1000)
        return report
    except subprocess.TimeoutExpired:
        raise CompileToolError("CODESYS compile batch timed out after %.0fs"
                               % timeout)
    finally:
        for p in (req_path, resp_path):
            try:
                os.remove(p)
            except OSError:
                pass


def compile_jobs(jobs, timeout: float = 300.0) -> dict:
    """Compile a batch of jobs in one CODESYS session.

    Each job: {"id", "pous": [{"name","kind","declaration","implementation"}],
               "auto_wire"?, "keep_project"?}
    Returns the full report dict; per-job results are in report["results"].
    """
    return _run_batch({"jobs": list(jobs)}, timeout=timeout)


def compile_st(name, implementation, declaration=None, kind=None,
               duts=None, job_id=None, auto_wire=True, keep_project=False,
               timeout: float = 300.0) -> dict:
    """Compile a single POU. Returns that job's result dict directly.

    - kind: "program" | "function_block" | "function"
            (guessed: PLC_PRG -> program, otherwise function_block)
    - duts: optional list of {"name","kind","declaration"} for structs/enums
            the POU depends on; created before the POU. kind defaults to
            "struct". declaration is the full "TYPE ... END_TYPE" text.
    - for FUNCTION, pass return type in the declaration header
      ("FUNCTION f : INT") or declaration stays as provided.
    """
    pou = {"name": name,
           "kind": kind,
           "declaration": declaration,
           "implementation": implementation}
    job = {"id": job_id or name, "pous": [pou],
           "auto_wire": auto_wire, "keep_project": keep_project}
    if duts:
        job["duts"] = list(duts)
    report = _run_batch({"jobs": [job]}, timeout=timeout)
    result = report["results"][0]
    result["client_elapsed_ms"] = report.get("client_elapsed_ms")
    return result


def _format_result(r: dict) -> str:
    lines = ["[%s] %s (%.2fs)%s"
             % ("PASS" if r["passed"] else "FAIL", r["id"],
                r.get("elapsed_ms", 0) / 1000.0,
                "  FATAL: " + r["fatal"] if r.get("fatal") else "")]
    for e in r.get("errors", []):
        loc = (" %s" % e["position_text"]) if e.get("position_text") else ""
        code = (" %s" % e["code"]) if e.get("code") else ""
        lines.append("   ERROR%s%s: %s" % (code, loc, e["text"]))
    for w in r.get("warnings", []):
        lines.append("   warning: %s" % w["text"])
    for ww in r.get("wire_warnings", []):
        lines.append("   wire-note: %s" % ww)
    return "\n".join(lines)


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print(__doc__)
        return EXIT_TOOL_ERROR
    with open(argv[0], "r", encoding="utf-8-sig") as f:
        request = json.load(f)
    if isinstance(request, dict) and "jobs" in request:
        jobs = request["jobs"]
    elif isinstance(request, list):
        jobs = request
    else:
        jobs = [request]
    try:
        report = compile_jobs(jobs)
    except CompileToolError as e:
        print("TOOL ERROR: %s" % e, file=sys.stderr)
        return EXIT_TOOL_ERROR

    out_path = argv[1] if len(argv) > 1 else None
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=1)

    for r in report["results"]:
        print(_format_result(r))
    print("----\nbatch %.1fs (%d job(s))"
          % (report.get("elapsed_ms", 0) / 1000.0, len(report["results"])))

    if any(r.get("fatal") for r in report["results"]):
        return EXIT_TOOL_ERROR
    return (EXIT_ALL_PASSED if all(r["passed"] for r in report["results"])
            else EXIT_BUILD_FAILED)


if __name__ == "__main__":
    sys.exit(main())
