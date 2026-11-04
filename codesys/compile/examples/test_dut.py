"""Regression test for the DUT / VAR_IN_OUT compile-service extensions.

Run:  python codesys/compile/examples/test_dut.py
Exit: 0 when all expectations hold, 1 otherwise.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from client import compile_jobs  # noqa: E402

ST_PUMP = (
    "TYPE ST_Pump :\n"
    "STRUCT\n"
    "    priority : INT;\n"
    "    selection : BOOL;\n"
    "    RunComd : BOOL;\n"
    "END_STRUCT\n"
    "END_TYPE\n"
)

PUMP_MODE = (
    "TYPE PumpMode :\n"
    "(\n"
    "    MODE_OFF,\n"
    "    MODE_MANUAL,\n"
    "    MODE_AUTO\n"
    ");\n"
    "END_TYPE\n"
)

FB_INOUT_DECL = (
    "FUNCTION_BLOCK PumpCtrlInOut\n"
    "VAR_IN_OUT\n    pumpGroup : ARRAY[1..5] OF ST_Pump;\nEND_VAR\n"
    "VAR_OUTPUT\n    anySelected : BOOL;\nEND_VAR\n"
)

JOBS = [
    {
        "id": "dut_struct_good",
        "duts": [{"name": "ST_Pump", "kind": "struct", "declaration": ST_PUMP}],
        "pous": [{
            "name": "PumpCtrl",
            "kind": "function_block",
            "declaration": (
                "FUNCTION_BLOCK PumpCtrl\n"
                "VAR\n    pumps : ARRAY[1..5] OF ST_Pump;\nEND_VAR\n"
                "VAR_OUTPUT\n    anySelected : BOOL;\nEND_VAR\n"),
            "implementation": "anySelected := pumps[1].selection;\n",
        }],
    },
    {
        "id": "var_inout_fb_autowire_skipped",
        "duts": [{"name": "ST_Pump", "kind": "struct", "declaration": ST_PUMP}],
        "pous": [{
            "name": "PumpCtrlInOut",
            "kind": "function_block",
            "declaration": FB_INOUT_DECL,
            "implementation": "anySelected := pumpGroup[1].selection;\n",
        }],
    },
    {
        "id": "var_inout_fb_bad_body_autowire_false_negative",
        "duts": [{"name": "ST_Pump", "kind": "struct", "declaration": ST_PUMP}],
        "pous": [{
            "name": "PumpCtrlInOut",
            "kind": "function_block",
            "declaration": FB_INOUT_DECL,
            "implementation": (
                "anySelected := pumpGroup[1].selection;\n"
                "bad_var := 1;\n"),
        }],
    },
    {
        "id": "var_inout_fb_caller_checks_body",
        "auto_wire": False,
        "duts": [{"name": "ST_Pump", "kind": "struct", "declaration": ST_PUMP}],
        "pous": [
            {
                "name": "PumpCtrlInOut",
                "kind": "function_block",
                "declaration": FB_INOUT_DECL,
                "implementation": (
                    "anySelected := pumpGroup[1].selection;\n"
                    "bad_var := 1;\n"),
            },
            {
                "name": "PLC_PRG",
                "kind": "program",
                "declaration": (
                    "PROGRAM PLC_PRG\n"
                    "VAR\n    fb : PumpCtrlInOut;\n"
                    "    arr : ARRAY[1..5] OF ST_Pump;\nEND_VAR\n"),
                "implementation": "fb(pumpGroup := arr);\n",
            },
        ],
    },
    {
        "id": "enum_good",
        "duts": [{"name": "PumpMode", "kind": "enum", "declaration": PUMP_MODE}],
        "pous": [{
            "name": "ModeUse",
            "kind": "function_block",
            "declaration": (
                "FUNCTION_BLOCK ModeUse\n"
                "VAR\n    m : PumpMode;\nEND_VAR\n"
                "VAR_OUTPUT\n    isAuto : BOOL;\nEND_VAR\n"),
            "implementation": "isAuto := (m = MODE_AUTO);\n",
        }],
    },
]

EXPECTED_PASSED = {
    "dut_struct_good": True,
    "var_inout_fb_autowire_skipped": True,
    "var_inout_fb_bad_body_autowire_false_negative": True,  # documented false negative
    "var_inout_fb_caller_checks_body": False,               # body is compiled here
    "enum_good": True,
}


def main():
    report = compile_jobs(JOBS)
    ok = True
    for r in report["results"]:
        rid = r["id"]
        exp = EXPECTED_PASSED[rid]
        good = (r["passed"] == exp) and not r.get("fatal")
        ok = ok and good
        print("[%s] %-42s passed=%-5s fatal=%-8s errors=%-2d wire=%s"
              % ("ok" if good else "CHECK", rid, r["passed"],
                 r.get("fatal") or "", len(r["errors"]), r.get("wire_warnings")))
        for e in r["errors"]:
            print("       ERROR %s %s: %s"
                  % (e["code"], e.get("position_text") or "", e["text"]))

    by_id = {r["id"]: r for r in report["results"]}

    skip = by_id["var_inout_fb_autowire_skipped"]
    assert any("VAR_IN_OUT" in w for w in skip["wire_warnings"]), \
        "expected a VAR_IN_OUT wire warning"

    false_neg = by_id["var_inout_fb_bad_body_autowire_false_negative"]
    assert false_neg["passed"] is True and \
        any("VAR_IN_OUT" in w for w in false_neg["wire_warnings"]), \
        "expected false negative (skipped, unwired) for bad VAR_IN_OUT body"

    caller = by_id["var_inout_fb_caller_checks_body"]
    assert caller["passed"] is False and len(caller["errors"]) > 0, \
        "caller mode must compile-check the VAR_IN_OUT FB body"

    print("----")
    print("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
