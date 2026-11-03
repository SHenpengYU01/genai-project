"""Generate a CODESYS ST self-test driver PROGRAM for a task.

Driver structure (one scan per test step, with ``repeat`` handled):

    IF NOT done THEN
        CASE tc OF ... set inputs + curRepeat ... END_CASE   (per step)
        fb(inputs := v_..., inouts := io_...);
        stepFail := FALSE;
        CASE tc OF ... stepFail := <mismatch exprs> ... END_CASE  (per step)
        repCnt := repCnt + 1;
        IF repCnt >= curRepeat THEN record pass/fail; advance END_IF
    END_IF

Results: CI_TEST_DRIVER.done / .allPass / .passCnt / .failCnt /
.firstFailTc / .firstFailStep, read back over the online API.

With ``generate(task, trace=True)`` the driver additionally records the actual
value of every output leaf (and of asserted inout leaves) at the end of each
step into ``tr_<name> : ARRAY[0..steps-1]`` variables plus a step counter
``si``; the values are read back symbol-by-symbol after the run (used by
``dataset/render_cases.py`` to fill the "实际输出" column).

Test-case array values are 0-indexed and map to LOWER_BOUND + i. Only keys
present in ``expect`` are compared.
"""
import json


def _base(t):
    return t.strip().split('(')[0].strip()


def _parse_array(t):
    s = t.strip()
    close = s.index(']')
    inner = s[s.index('[') + 1:close].strip()
    rest = s[close + 1:].strip()
    if rest.upper().startswith('OF'):
        rest = rest[2:].strip()
    bounds = None if inner == '*' else \
        tuple(int(x.strip()) for x in inner.split('..'))
    return bounds, rest


def _classify(t, struct_names):
    s = t.strip()
    if s.upper().startswith('ARRAY['):
        bounds, elem = _parse_array(s)
        return {'kind': 'array', 'bounds': bounds,
                'elem': _classify(elem, struct_names)}
    base = _base(s)
    if base in struct_names:
        return {'kind': 'struct', 'name': base}
    return {'kind': 'scalar', 'type': s}


def _literal(value, t):
    b = _base(t).upper()
    if b == 'BOOL':
        return 'TRUE' if value else 'FALSE'
    if b == 'LTIME' and isinstance(value, str) and value.upper().startswith('T#'):
        return 'LTIME#' + value[2:]
    if b in ('TIME', 'DATE', 'TIME_OF_DAY', 'TOD', 'DATE_AND_TIME', 'DT'):
        if isinstance(value, str):
            return value
    if b.startswith('STRING') or b.startswith('WSTRING'):
        return "'%s'" % str(value)
    if b in ('CHAR', 'WCHAR'):
        return "'%s'" % str(value)
    if isinstance(value, bool):
        return 'TRUE' if value else 'FALSE'
    if isinstance(value, float):
        return repr(value)
    return str(value)


def _assign_lines(target, value, tinfo, duts_map, indent):
    k = tinfo['kind']
    if k == 'scalar':
        return [indent + "%s := %s;" % (target, _literal(value, tinfo['type']))]
    if k == 'struct':
        lines = []
        for f, fv in value.items():
            ft = duts_map[tinfo['name']][f]
            lines += _assign_lines("%s.%s" % (target, f), fv,
                                   _classify(ft, set(duts_map)), duts_map, indent)
        return lines
    lo = tinfo['bounds'][0] if tinfo['bounds'] else 1
    lines = []
    for j, ev in enumerate(value):
        lines += _assign_lines("%s[%d]" % (target, lo + j), ev,
                               tinfo['elem'], duts_map, indent)
    return lines


def _mismatch_exprs(actual, value, tinfo, duts_map):
    k = tinfo['kind']
    if k == 'scalar':
        return ["(%s <> %s)" % (actual, _literal(value, tinfo['type']))]
    if k == 'struct':
        out = []
        for f, fv in value.items():
            ft = duts_map[tinfo['name']][f]
            out += _mismatch_exprs("%s.%s" % (actual, f), fv,
                                   _classify(ft, set(duts_map)), duts_map)
        return out
    lo = tinfo['bounds'][0] if tinfo['bounds'] else 1
    out = []
    for j, ev in enumerate(value):
        out += _mismatch_exprs("%s[%d]" % (actual, lo + j), ev,
                               tinfo['elem'], duts_map)
    return out


def _leaf_pairs(actual, value, tinfo, duts_map):
    """Flatten an asserted value into [(st_expr, st_type, python_value)]."""
    k = tinfo['kind']
    if k == 'scalar':
        return [(actual, tinfo['type'], value)]
    if k == 'struct':
        out = []
        for f, fv in value.items():
            ft = duts_map[tinfo['name']][f]
            out += _leaf_pairs("%s.%s" % (actual, f), fv,
                               _classify(ft, set(duts_map)), duts_map)
        return out
    lo = tinfo['bounds'][0] if tinfo['bounds'] else 1
    out = []
    for j, ev in enumerate(value):
        out += _leaf_pairs("%s[%d]" % (actual, lo + j), ev,
                           tinfo['elem'], duts_map)
    return out


def _leaves_of(actual, tinfo, duts_map):
    """Flatten a typed output/inout without a sample value (bounds must exist)."""
    k = tinfo['kind']
    if k == 'scalar':
        return [(actual, tinfo['type'])]
    if k == 'struct':
        out = []
        for f, ft in duts_map[tinfo['name']].items():
            out += _leaves_of("%s.%s" % (actual, f),
                              _classify(ft, set(duts_map)), duts_map)
        return out
    if tinfo['bounds'] is None:          # ARRAY[*] needs a sample to size it
        return []
    out = []
    for i in range(tinfo['bounds'][0], tinfo['bounds'][1] + 1):
        out += _leaves_of("%s[%d]" % (actual, i), tinfo['elem'], duts_map)
    return out


def _trace_name(expr):
    """fb[tc].Motor -> tr_Motor ; io_pumpGroup[tc][1].RunComd -> tr_pumpGroup_1_RunComd"""
    if expr.startswith("fb[tc]."):
        rest = expr[len("fb[tc]."):]
    elif expr.startswith("io_"):
        rest = expr[3:]
        if "[tc]" in rest:
            head, tail = rest.split("[tc]", 1)
            rest = head + tail
    else:
        rest = expr
    for ch in "[].":
        rest = rest.replace(ch, "_")
    while "__" in rest:          # CODESYS 对连续下划线不友好，压成单个
        rest = rest.replace("__", "_")
    return "tr_%s" % rest.strip("_")


def trace_specs(task):
    """Leaves to record while tracing: all outputs + asserted inout leaves.

    Returns a list of dicts {var, expr, type, path}; `path` is the readable
    key used in the test-case document (e.g. ``pumpGroup[1].RunComd``).
    """
    itf = task['interface']
    duts = {d['name']: {f['name']: f['type'] for f in d.get('fields', [])}
            for d in itf.get('duts', [])}
    struct_names = set(duts)
    out_info = {e['name']: _classify(e['type'], struct_names)
                for e in itf['outputs']}
    io_info = {e['name']: _classify(e['type'], struct_names)
               for e in itf['inouts']}

    pairs = []      # (expr, st_type, path)
    for name, tinfo in out_info.items():
        for expr, st_type in _leaves_of("fb[tc].%s" % name, tinfo, duts):
            path = expr[len("fb[tc]."):]
            pairs.append((expr, st_type, path))
    asserted = {}
    for tc in task['test_cases']:
        for st in tc['steps']:
            for key, val in st['expect'].items():
                if key in io_info:
                    for e, t, _ in _leaf_pairs("io_%s[tc]" % key, val,
                                               io_info[key], duts):
                        asserted[e] = t
    for expr, st_type in asserted.items():
        path = expr.replace("io_", "", 1).replace("[tc]", "", 1)
        pairs.append((expr, st_type, path))

    specs, seen = [], {}
    for expr, st_type, path in pairs:
        var = _trace_name(expr)
        if var in seen:
            if seen[var] == expr:
                continue
            n = 2
            while "%s_%d" % (var, n) in seen:
                n += 1
            var = "%s_%d" % (var, n)
        seen[var] = expr
        specs.append({"var": var, "expr": expr, "type": st_type,
                      "path": path})
    return specs


def _concrete_type(name, tinfo, entry, test_cases):
    if tinfo['kind'] != 'array' or tinfo['bounds'] is not None:
        return entry['type'].strip()
    cap = entry.get('capacity') or 1
    for tc in test_cases:
        for st in tc['steps']:
            for src in (st['inputs'], st['expect']):
                v = src.get(name)
                if isinstance(v, list):
                    cap = max(cap, len(v))
    _, elem = _parse_array(entry['type'])
    return "ARRAY[1..%d] OF %s" % (cap, elem)


def generate(task, trace=False):
    fb = task['pou']['name']
    itf = task['interface']
    duts = {d['name']: {f['name']: f['type'] for f in d.get('fields', [])}
            for d in itf.get('duts', [])}
    struct_names = set(duts)
    inputs = itf['inputs']
    outputs = itf['outputs']
    inouts = itf['inouts']
    cases = task['test_cases']
    specs = trace_specs(task) if trace else []
    n_steps_total = sum(len(c['steps']) for c in cases)

    in_info = {e['name']: _classify(e['type'], struct_names) for e in inputs}
    out_info = {e['name']: _classify(e['type'], struct_names) for e in outputs}
    io_entries = {e['name']: e for e in inouts}
    io_info = {e['name']: _classify(e['type'], struct_names) for e in inouts}
    io_type = {n: _concrete_type(n, io_info[n], io_entries[n], cases)
               for n in io_info}

    L = []
    a = L.append
    a("PROGRAM CI_TEST_DRIVER")
    a("VAR")
    a("    fb : ARRAY[0..%d] OF %s;" % (len(cases) - 1, fb))
    a("    step : INT := 0;")
    a("    repCnt : INT := 0;")
    a("    tc : INT := 0;")
    a("    done : BOOL := FALSE;")
    a("    allPass : BOOL := TRUE;")
    a("    passCnt : INT := 0;")
    a("    failCnt : INT := 0;")
    a("    firstFailTc : INT := -1;")
    a("    firstFailStep : INT := -1;")
    a("    curRepeat : INT := 1;")
    a("    curLen : INT := 0;")
    a("    stepFail : BOOL;")
    if trace:
        a("    si : INT := 0;")
        for sp in specs:
            a("    %s : ARRAY[0..%d] OF %s;"
              % (sp['var'], max(n_steps_total - 1, 0), sp['type']))
    for e in inputs:
        a("    v_%s : %s;" % (e['name'], e['type']))
    for e in inouts:
        a("    io_%s : ARRAY[0..%d] OF %s;"
          % (e['name'], len(cases) - 1, io_type[e['name']]))
    # scalar values captured at the first failing step (feedback for the agent)
    scalars = [(e['name'], e['type'], "fb[tc].%s" % e['name'])
               for e in outputs if out_info[e['name']]['kind'] == 'scalar']
    scalars += [(e['name'], io_type[e['name']], "io_%s[tc]" % e['name'])
                for e in inouts if io_info[e['name']]['kind'] == 'scalar']
    for n, t, _ in scalars:
        a("    fail_%s : %s;" % (n, t))
    a("END_VAR")
    a("")
    a("IF NOT done THEN")
    a("    (* set inputs for the current step *)")
    a("    CASE tc OF")
    for i, tc in enumerate(cases):
        a("    %d:" % i)
        a("        CASE step OF")
        for s, st in enumerate(tc['steps']):
            a("        %d:" % s)
            for e in inputs:
                v = st['inputs'].get(e['name'])
                if v is not None:
                    for ln in _assign_lines("v_%s" % e['name'], v,
                                            in_info[e['name']], duts, "            "):
                        a(ln)
            for e in inouts:
                v = st['inputs'].get(e['name'])
                if v is not None:
                    for ln in _assign_lines("io_%s[tc]" % e['name'], v,
                                            io_info[e['name']], duts, "            "):
                        a(ln)
            a("            curRepeat := %d;" % st.get('repeat', 1))
        a("        END_CASE")
        a("        curLen := %d;" % len(tc['steps']))
    a("    END_CASE")
    a("")
    args = []
    for e in inputs:
        args.append("%s := v_%s" % (e['name'], e['name']))
    for e in inouts:
        args.append("%s := io_%s[tc]" % (e['name'], e['name']))
    a("    fb[tc](%s);" % ", ".join(args))
    a("")
    a("    (* compare outputs for the current step *)")
    a("    stepFail := FALSE;")
    a("    CASE tc OF")
    for i, tc in enumerate(cases):
        a("    %d:" % i)
        a("        CASE step OF")
        for s, st in enumerate(tc['steps']):
            exprs = []
            for key, val in st['expect'].items():
                if key in out_info:
                    actual = "fb[tc].%s" % key
                    tinfo = out_info[key]
                elif key in io_info:
                    actual = "io_%s[tc]" % key
                    tinfo = io_info[key]
                else:
                    continue
                exprs += _mismatch_exprs(actual, val, tinfo, duts)
            a("        %d:" % s)
            a("            stepFail := %s;"
              % (" OR ".join(exprs) if exprs else "FALSE"))
        a("        END_CASE")
    a("    END_CASE")
    a("")
    a("    repCnt := repCnt + 1;")
    a("    IF repCnt >= curRepeat THEN")
    a("        IF stepFail THEN")
    a("            allPass := FALSE;")
    a("            failCnt := failCnt + 1;")
    a("            IF firstFailTc < 0 THEN")
    a("                firstFailTc := tc;")
    a("                firstFailStep := step;")
    for n, _, src in scalars:
        a("                fail_%s := %s;" % (n, src))
    a("            END_IF")
    a("        ELSE")
    a("            passCnt := passCnt + 1;")
    a("        END_IF")
    if trace:
        for sp in specs:
            a("        %s[si] := %s;" % (sp['var'], sp['expr']))
        a("        si := si + 1;")
    a("        repCnt := 0;")
    a("        step := step + 1;")
    a("        IF step >= curLen THEN")
    a("            step := 0;")
    a("            tc := tc + 1;")
    a("            IF tc >= %d THEN" % len(cases))
    a("                done := TRUE;")
    a("            END_IF")
    a("        END_IF")
    a("    END_IF")
    a("END_IF")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    import sys
    task = json.load(open(sys.argv[1], encoding="utf-8"))
    print(generate(task))
