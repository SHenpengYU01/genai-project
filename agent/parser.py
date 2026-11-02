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


_TYPE_RE = re.compile(
    r"\bTYPE\s+([A-Za-z_]\w*)\s*:(.*?)\bEND_TYPE\b", re.I | re.S)
_HEADER = re.compile(
    r"^\s*(FUNCTION_BLOCK|PROGRAM|FUNCTION)\s+([A-Za-z_]\w*)", re.I)
_VAR_OPEN = re.compile(
    r"^VAR(_INPUT|_OUTPUT|_IN_OUT|_PERSISTENT|_CONSTANT|_GLOBAL|_ACCESS)?\b",
    re.I)


def _strip_fences(text):
    return "\n".join(ln for ln in text.splitlines()
                     if not ln.strip().startswith("```"))


def _fallback_parse(text):
    """Parse plain ST (no <<<>>> markers): TYPE blocks + the first POU.

    Declaration is taken through the last leading END_VAR; the remainder is
    the implementation body. Used when the model ignores the block format.
    """
    clean = _strip_fences(text)
    duts = []
    for m in _TYPE_RE.finditer(clean):
        body = m.group(2)
        kind = "struct" if re.search(r"\bSTRUCT\b", body, re.I) else "struct"
        decl = ("TYPE %s :%s END_TYPE" % (m.group(1), body)).strip()
        duts.append({"name": m.group(1), "kind": kind,
                     "declaration": decl + "\n"})

    pous = []
    lines = clean.splitlines()
    for i, ln in enumerate(lines):
        m = _HEADER.match(ln)
        if not m:
            continue
        kind = {"function_block": "function_block", "program": "program",
                "function": "function"}[m.group(1).lower()]
        name = m.group(2)
        last_end = i
        impl_start = None
        in_var = False
        j = i + 1
        while j < len(lines):
            s = lines[j].strip()
            if _VAR_OPEN.match(s):
                in_var = True
            elif re.match(r"^END_VAR\b", s, re.I):
                in_var = False
                last_end = j
            elif in_var:
                pass
            elif not s or s.startswith("(*") or s.startswith("//"):
                pass
            else:
                impl_start = j
                break
            j += 1
        if impl_start is None:
            impl_start = j
        decl = "\n".join(lines[i:last_end + 1]).strip() + "\n"
        impl = "\n".join(lines[impl_start:]).strip()
        pous.append({"name": name, "kind": kind,
                     "declaration": decl,
                     "implementation": (impl + "\n") if impl else ""})
        break
    return {"duts": duts, "pous": pous, "errors": []}


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
    if not pous and not duts and not errors:
        fb = _fallback_parse(text)
        if fb["pous"] or fb["duts"]:
            return fb
    if not pous and not duts:
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


VALID_DUT_KINDS = {"struct", "structure", "enum", "enumeration",
                   "alias", "union"}

_BUILTIN_TYPES = {
    "BOOL", "BIT", "BYTE", "WORD", "DWORD", "LWORD", "SINT", "USINT", "INT",
    "UINT", "DINT", "UDINT", "LINT", "ULINT", "REAL", "LREAL", "TIME",
    "LTIME", "DATE", "TOD", "DT", "STRING", "WSTRING", "CHAR", "WCHAR",
    "POINTER", "ARRAY", "VARIANT", "ANY",
}


def check_duts(duts):
    """Reject invalid DUT kinds and names that collide with built-in types."""
    errors = []
    for d in duts:
        kind = (d.get("kind") or "").strip().lower()
        if kind not in VALID_DUT_KINDS:
            errors.append("DUT '%s' 的 kind '%s' 无效（应为 struct/enum/alias/union）"
                          % (d["name"], d.get("kind")))
        if d["name"].upper() in _BUILTIN_TYPES:
            errors.append("DUT 名 '%s' 与内置类型冲突，请另起名称"
                          % d["name"])
    return errors


def check_names(pous, duts):
    """Structural errors: duplicate POU names or POU/DUT name collisions."""
    errors = []
    seen = set()
    for p in pous:
        key = p["name"].lower()
        if key in seen:
            errors.append("POU 名重复：'%s'" % p["name"])
        seen.add(key)
    dut_names = {d["name"].lower() for d in duts}
    for p in pous:
        if p["name"].lower() in dut_names:
            errors.append("POU '%s' 与同名的 DUT 冲突，请改用不同的名称"
                          % p["name"])
    return errors


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
