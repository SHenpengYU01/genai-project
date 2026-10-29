"""Generate scripted mock model outputs from the dataset reference solutions.

mocks/reference/<id>.json      : one response = the reference solution
mocks/broken_once/<id>.json    : first response has an undeclared variable,
                                 second response = the reference solution

Run:  python experiments/build_mocks.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TASKS = os.path.join(ROOT, "dataset", "tasks")


def ref_blocks(task):
    ref = task["reference"]
    parts = []
    for d in ref.get("duts", []):
        parts.append("<<<DUT name=%s kind=%s>>>\n%s\n<<<END>>>"
                     % (d["name"], d.get("kind", "struct"),
                        d["declaration"].strip()))
    for p in ref.get("pous", []):
        if p["name"] != task["pou"]["name"]:
            continue
        parts.append("<<<POU name=%s kind=%s>>>\n%s<<<IMPL>>>\n%s\n<<<END>>>"
                     % (p["name"], p["kind"],
                        p["declaration"].strip() + "\n",
                        p["implementation"].strip()))
    return "\n\n".join(parts)


def broken_blocks(task):
    """Reference with one undeclared-variable line injected (compile error)."""
    ref = task["reference"]
    parts = []
    for d in ref.get("duts", []):
        parts.append("<<<DUT name=%s kind=%s>>>\n%s\n<<<END>>>"
                     % (d["name"], d.get("kind", "struct"),
                        d["declaration"].strip()))
    for p in ref.get("pous", []):
        if p["name"] != task["pou"]["name"]:
            continue
        impl = p["implementation"].strip().splitlines()
        impl = [impl[0], "(* intentional bug for mock *)",
                "mock_undeclared_var_xyz := 1;"] + impl[1:]
        parts.append("<<<POU name=%s kind=%s>>>\n%s<<<IMPL>>>\n%s\n<<<END>>>"
                     % (p["name"], p["kind"],
                        p["declaration"].strip() + "\n",
                        "\n".join(impl)))
    return "\n\n".join(parts)


def _sabotage_lines(task):
    """Assignments that compile but break behavior (for test-feedback tests)."""
    lines = ["(* intentional behavior bug for mock *)"]
    for e in task["interface"].get("outputs", []):
        t = e["type"].strip().upper()
        if t == "BOOL":
            lines.append("%s := FALSE;" % e["name"])
        elif t.startswith(("INT", "UINT", "WORD", "DWORD", "LINT", "ULINT",
                           "SINT", "USINT", "BYTE", "DINT", "UDINT", "REAL",
                           "LREAL")):
            lines.append("%s := 0;" % e["name"])
    return lines


def sabotage_blocks(task):
    """Reference plus output overrides at the end (compiles, tests must fail)."""
    ref = task["reference"]
    parts = []
    for d in ref.get("duts", []):
        parts.append("<<<DUT name=%s kind=%s>>>\n%s\n<<<END>>>"
                     % (d["name"], d.get("kind", "struct"),
                        d["declaration"].strip()))
    for p in ref.get("pous", []):
        if p["name"] != task["pou"]["name"]:
            continue
        impl = p["implementation"].strip().splitlines()
        impl = impl + _sabotage_lines(task)
        parts.append("<<<POU name=%s kind=%s>>>\n%s<<<IMPL>>>\n%s\n<<<END>>>"
                     % (p["name"], p["kind"],
                        p["declaration"].strip() + "\n",
                        "\n".join(impl)))
    return "\n\n".join(parts)


def main():
    for kind in ("reference", "broken_once", "test_fail_once"):
        os.makedirs(os.path.join(HERE, "mocks", kind), exist_ok=True)
    n = 0
    for fn in sorted(os.listdir(TASKS)):
        if not fn.endswith(".json") or fn == "example_motor.json":
            continue
        task = json.load(open(os.path.join(TASKS, fn), encoding="utf-8"))
        good = ref_blocks(task)
        with open(os.path.join(HERE, "mocks", "reference",
                               task["id"] + ".json"), "w",
                  encoding="utf-8") as f:
            json.dump({"responses": [good]}, f, ensure_ascii=False, indent=1)
        with open(os.path.join(HERE, "mocks", "broken_once",
                               task["id"] + ".json"), "w",
                  encoding="utf-8") as f:
            json.dump({"responses": [broken_blocks(task), good]},
                      f, ensure_ascii=False, indent=1)
        with open(os.path.join(HERE, "mocks", "test_fail_once",
                               task["id"] + ".json"), "w",
                  encoding="utf-8") as f:
            json.dump({"responses": [sabotage_blocks(task), good]},
                      f, ensure_ascii=False, indent=1)
        n += 1
    print("wrote %d mock triples" % n)


if __name__ == "__main__":
    main()
