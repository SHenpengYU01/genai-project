"""Generate a PLC_PRG caller so the FB under test is really compiled.

CODESYS only compiles POUs reachable from a task. For VAR_IN_OUT FBs the
compile service's auto_wire cannot call them, so the harness overrides the
template's PLC_PRG with a caller that instantiates the FB and binds every
parameter (scalars as literals, arrays/structs through declared variables).
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "codesys", "simulate"))
import driver as dg  # noqa: E402  (codesys/simulate/driver.py)


def _default_literal(t):
    b = dg._base(t).upper()
    if b == "BOOL":
        return "FALSE"
    if b == "TIME":
        return "T#0s"
    if b == "LTIME":
        return "LTIME#0ms"
    if b == "DATE":
        return "D#1970-01-01"
    if b in ("TOD", "TIME_OF_DAY"):
        return "TOD#00:00:00"
    if b in ("DT", "DATE_AND_TIME"):
        return "DT#1970-01-01-00:00:00"
    if b.startswith(("STRING", "WSTRING", "CHAR", "WCHAR")):
        return "''"
    return "0"


def generate(task):
    fb = task["pou"]["name"]
    itf = task["interface"]
    duts = {d["name"]: {f["name"]: f["type"] for f in d.get("fields", [])}
            for d in itf.get("duts", [])}
    struct_names = set(duts)

    decls = ["PROGRAM PLC_PRG", "VAR", "    fb : %s;" % fb]
    args = []
    for e in itf.get("inputs", []):
        info = dg._classify(e["type"], struct_names)
        if info["kind"] == "scalar":
            args.append("%s := %s" % (e["name"], _default_literal(e["type"])))
        else:
            decls.append("    in_%s : %s;" % (e["name"], e["type"]))
            args.append("%s := in_%s" % (e["name"], e["name"]))
    for e in itf.get("inouts", []):
        info = dg._classify(e["type"], struct_names)
        t = dg._concrete_type(e["name"], info, e, task.get("test_cases", []))
        decls.append("    %s : %s;" % (e["name"], t))
        args.append("%s := %s" % (e["name"], e["name"]))
    decls.append("END_VAR")

    body = ["fb(%s);" % ", ".join(args)]
    return {"name": "PLC_PRG", "kind": "program",
            "declaration": "\n".join(decls) + "\n",
            "implementation": "\n".join(body) + "\n"}
