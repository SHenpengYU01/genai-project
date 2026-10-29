"""Parse the model's file-block output into compile-service POUs/DUTs.

Expected block format (also described in prompt.FORMAT_SPEC):

    <<<DUT name=ST_Pump kind=struct>>>
    TYPE ST_Pump : ... END_TYPE
    <<<END>>>

    <<<POU name=MotorCtrl kind=function_block>>>
    FUNCTION_BLOCK MotorCtrl
    VAR_INPUT ... END_VAR
    <<<IMPL>>>
    <statement body>
    <<<END>>>
"""
from __future__ import annotations

import re

_OPEN = re.compile(
    r"^\s*<<<\s*(DUT|POU)\s+name\s*=\s*([A-Za-z0-9_]+)"
    r"\s+kind\s*=\s*([A-Za-z0-9_]+)\s*>>>\s*$", re.I)
_IMPL = re.compile(r"^\s*<<<\s*IMPL\s*>>>\s*$", re.I)
_END = re.compile(r"^\s*<<<\s*END\s*>>>\s*$", re.I)


def parse(text):
    """Return {"duts": [...], "pous": [...], "errors": [str, ...]}."""
    duts, pous, errors = [], [], []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = _OPEN.match(lines[i])
        if not m:
            i += 1
            continue
        kind_tag, name, kind = m.group(1).upper(), m.group(2), m.group(3).lower()
        i += 1
        decl_lines, impl_lines = [], []
        target = decl_lines
        closed = False
        while i < len(lines):
            if _IMPL.match(lines[i]):
                target = impl_lines
                i += 1
                continue
            if _END.match(lines[i]):
                closed = True
                i += 1
                break
            target.append(lines[i])
            i += 1
        if not closed:
            errors.append("块 '%s' 缺少 <<<END>>>" % name)
        decl = "\n".join(decl_lines).strip()
        impl = "\n".join(impl_lines).strip()
        if kind_tag == "DUT":
            if not decl:
                errors.append("DUT '%s' 声明为空" % name)
                continue
            duts.append({"name": name, "kind": kind, "declaration": decl})
        else:
            if not decl:
                errors.append("POU '%s' 声明为空" % name)
                continue
            pous.append({"name": name, "kind": kind,
                         "declaration": decl + "\n",
                         "implementation": (impl + "\n") if impl else ""})
    if not pous:
        errors.append("未找到任何 POU 块（输出格式不符合要求）")
    return {"duts": duts, "pous": pous, "errors": errors}


# ---------------------------------------------------------------------------
# Interface compliance check (before paying for a CODESYS compile)
# ---------------------------------------------------------------------------
_SECTION = re.compile(
    r"VAR_(INPUT|OUTPUT|IN_OUT)\b(.*?)END_VAR", re.I | re.S)


def _norm_type(t):
    return re.sub(r"\s+", "", t).upper()


def _parse_section(body):
    """Parse 'a, b : INT; c : BOOL := TRUE;' into [(names, type)]."""
    out = []
    for chunk in re.split(r";", body):
        chunk = re.sub(r"\(\*.*?\*\)", " ", chunk, flags=re.S)
        chunk = chunk.split("(*")[0]
        if ":" not in chunk:
            continue
        names_part, _, rest = chunk.partition(":")
        rest = rest.split(":=")[0].strip()
        if not rest:
            continue
        for n in names_part.replace("\n", " ").split(","):
            n = n.strip()
            if n:
                out.append((n, rest.strip()))
    return out


def interface_sections(declaration):
    secs = {"input": {}, "output": {}, "inout": {}}
    for m in _SECTION.finditer(declaration or ""):
        key = {"INPUT": "input", "OUTPUT": "output",
               "IN_OUT": "inout"}[m.group(1).upper()]
        for n, t in _parse_section(m.group(2)):
            secs[key][n.lower()] = t
    return secs


def check_interface(task, pous):
    """Return list of human-readable interface errors (empty = OK)."""
    errors = []
    fb_name = task["pou"]["name"]
    target = None
    for p in pous:
        if p["name"].lower() == fb_name.lower():
            target = p
            break
    if target is None:
        return ["缺少题目要求的 POU '%s'" % fb_name]
    if target["name"] != fb_name:
        errors.append("POU 名应为 '%s'，实际为 '%s'"
                      % (fb_name, target["name"]))
    secs = interface_sections(target["declaration"])
    for group, iface_key in (("inputs", "input"), ("outputs", "output"),
                             ("inouts", "inout")):
        for e in task["interface"].get(group, []):
            got = secs[iface_key].get(e["name"].lower())
            if got is None:
                errors.append("接口缺少 %s 参数 '%s'（应为 %s）"
                              % (iface_key.upper(), e["name"], e["type"]))
            elif _norm_type(got) != _norm_type(e["type"]):
                errors.append("参数 '%s' 类型应为 '%s'，实际为 '%s'"
                              % (e["name"], e["type"], got))
    return errors
