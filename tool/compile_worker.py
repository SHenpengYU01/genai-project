# Stateless batch ST compile worker for CODESYS.
#
# Invocation (via run_compile.bat):
#   CODESYS.exe --profile=... --runscript=compile_worker.py
#               --scriptargs:'<request.json> <response.json>' --noUI
#
# IMPORTANT compiler behaviour (verified on CODESYS 3.5 SP22 P4):
#   rebuild() only compiles POUs reachable from a task's call graph.
#   A standalone FUNCTION_BLOCK / FUNCTION / PROGRAM with a syntax error
#   reports ZERO errors unless it is wired into a task. This worker therefore
#   generates a hidden harness PROGRAM "CI_HARNESS_PRG" on MainTask that instantiates
#   every FB and calls every FB/FUNCTION in the job, and adds every extra
#   PROGRAM to MainTask as well. Disable with job flag "auto_wire": false.
#
# Request JSON (UTF-8), either { "jobs": [ ... ] } or one bare job object:
#   { "id": "case001",
#     "auto_wire": true,            # default true
#     "keep_project": false,        # keep the filled project copy for debug
#     "duts": [                     # optional: structs/enums the POUs depend on
#       { "name": "ST_Pump", "kind": "struct",
#         "declaration": "TYPE ST_Pump :\nSTRUCT ... END_STRUCT\nEND_TYPE" } ],
#     "pous": [
#       { "name": "MotorCtrl", "kind": "function_block",
#         "declaration": "FUNCTION_BLOCK MotorCtrl\nVAR_INPUT ...",
#         "implementation": "..." },
#       { "name": "PLC_PRG", "kind": "program", "declaration": "...",
#         "implementation": "..." }
#     ] }
#   kind: program | function_block | function (guessed: PLC_PRG->program,
#         everything else->function_block). FUNCTION return type is parsed
#         from the declaration header ("FUNCTION f : INT") or "return_type".
#
# Response JSON (UTF-8):
#   { "ok": true, "elapsed_ms": N, "error": null,
#     "results": [ { "id", "passed", "fatal", "elapsed_ms",
#                    "errors": [ {severity, category, text, code,
#                                 position, length, position_text} ],
#                    "warnings": [ ... ], "info_count",
#                    "wire_warnings": [ ... ], "project_copy" } ] }
#
# Keep this file ASCII-only (IronPython 2.7 PEP 263 parse rule).
import sys
import os
import re
import json
import System
from scriptengine import *

REQ = sys.argv[1] if len(sys.argv) > 1 else None
RESP = sys.argv[2] if len(sys.argv) > 2 else None

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "template.project")
WORKDIR = os.path.join(HERE, "work")
# NOTE: CODESYS rejects identifiers starting with underscores ("identifier is
# not valid for this object"), so the harness and its locals use letter-first
# names. CI_HARNESS_PRG is reserved the same way __CI_PRG was.
HARNESS = "CI_HARNESS_PRG"

NUMERIC_TYPES = set([
    "SINT", "USINT", "INT", "UINT", "DINT", "UDINT", "LINT", "ULINT",
    "BYTE", "WORD", "DWORD", "LWORD", "REAL", "LREAL",
])


def ticks():
    return System.Diagnostics.Stopwatch.GetTimestamp()


def elapsed_ms(start):
    return int((ticks() - start) * 1000.0
               / System.Diagnostics.Stopwatch.Frequency)


def terminate(code):
    def kill(state):
        try:
            System.Diagnostics.Process.GetCurrentProcess().Kill()
        except Exception:
            pass

    System.Threading.Timer(
        System.Threading.TimerCallback(kill), None, 3000,
        System.Threading.Timeout.Infinite)
    System.Environment.Exit(code)


def write_json(path, obj):
    text = json.dumps(obj, ensure_ascii=False, indent=1)
    System.IO.File.WriteAllText(path, text, System.Text.UTF8Encoding(False))


def classify(sev):
    v = int(sev)
    if v & 3:
        return "error"
    if v & 4:
        return "warning"
    return "info"


def attr_str(o, name):
    try:
        v = getattr(o, name)
        if v is None:
            return None
        return str(v)
    except Exception:
        return None


def message_text(o):
    return attr_str(o, "message") or attr_str(o, "text") or str(o)


def collect_diagnostics():
    errors, warnings = [], []
    info_count = 0
    for cat in (system.get_message_categories(True) or []):
        guid = cat.ToString()
        try:
            desc = str(system.get_message_category_description(cat))
        except Exception:
            desc = ""
        try:
            objs = system.get_message_objects(guid)
        except Exception:
            continue
        for o in objs:
            try:
                kind = classify(o.severity)
            except Exception:
                kind = "info"
            if kind == "info":
                info_count += 1
                continue
            prefix = attr_str(o, "prefix") or ""
            number = attr_str(o, "number") or ""
            rec = {
                "severity": attr_str(o, "severity") or "",
                "category": desc,
                "text": message_text(o),
                "code": (prefix + number) if number else "",
                "position_text": attr_str(o, "position_text"),
                "position": attr_str(o, "position"),
                "length": attr_str(o, "length"),
            }
            (errors if kind == "error" else warnings).append(rec)
    return errors, warnings, info_count


_safe_id = re.compile(r"[^A-Za-z0-9_\-]")


def job_project_path(job_id):
    name = _safe_id.sub("_", str(job_id or "job"))[:40]
    if not System.IO.Directory.Exists(WORKDIR):
        System.IO.Directory.CreateDirectory(WORKDIR)
    return os.path.join(WORKDIR, "%s_%d.project" % (name, ticks()))


def normalize_kind(kind, pou_name):
    k = (str(kind).strip().lower().replace("-", "_").replace(" ", "_")
         if kind else "")
    if k in ("program", "prg"):
        return "program"
    if k in ("function", "fun", "func"):
        return "function"
    if k in ("function_block", "functionblock", "fb"):
        return "function_block"
    if k:
        raise ValueError("unknown POU kind: %r" % kind)
    return "program" if pou_name == "PLC_PRG" else "function_block"


def pou_kind_enum(kind):
    return {"program": PouType.Program,
            "function_block": PouType.FunctionBlock,
            "function": PouType.Function}[kind]


def find_pou(proj, name):
    try:
        hits = proj.find(name, True)
        for h in (hits or []):
            try:
                if h.get_name() == name:
                    return h
            except Exception:
                return h
        if hits:
            return hits[0]
    except Exception:
        pass
    return None


def replace_doc(doc, text):
    if text is None:
        return
    try:
        doc.replace(text)
        return
    except Exception:
        pass
    doc.text = text


_FUNC_RETURN_RE = re.compile(
    r"FUNCTION\s+[A-Za-z_]\w*\s*:\s*([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)


def function_return_type(spec):
    rt = spec.get("return_type")
    if rt:
        return str(rt)
    m = _FUNC_RETURN_RE.search(spec.get("declaration") or "")
    if m:
        return m.group(1)
    raise ValueError("FUNCTION '%s': cannot parse return type from "
                     "declaration header; set 'return_type' explicitly"
                     % spec.get("name"))


def default_literal(type_name):
    """Default argument literal for an IEC simple type, or None if unsure."""
    t = type_name.strip().upper()
    if t == "BOOL":
        return "FALSE"
    if t in NUMERIC_TYPES:
        return "0"
    if t in ("TIME", "LTIME"):
        return "T#0s"
    if t in ("DATE",):
        return "D#0001-01-01"
    if t in ("TIME_OF_DAY", "TOD", "DATE_AND_TIME", "DT"):
        return "TOD#00:00:00"
    if t.startswith("STRING") or t.startswith("WSTRING") or t in ("CHAR", "WCHAR"):
        return "''"
    return None


_VAR_SECTION_RE = re.compile(r"VAR(_INPUT|_OUTPUT|_IN_OUT|_PERSISTENT|_CONSTANT|_GLOBAL|_ACCESS)?\s*(?:CONSTANT|RETAIN|PERSISTENT)?\s*\n(.*?)END_VAR",
                             re.IGNORECASE | re.DOTALL)


def has_var_in_out(declaration):
    return re.search(r"VAR_IN_OUT\b", declaration or "", re.IGNORECASE) is not None


def function_input_args(declaration):
    """Return list of argument literals to call the function, or None if the
    signature cannot be wired safely (IN_OUTs, arrays, structs, unknown types).
    Functions with VAR_INPUT constants/enums fall back to None as well."""
    if has_var_in_out(declaration):
        return None
    args = []
    for m in _VAR_SECTION_RE.finditer(declaration or ""):
        qualifier = (m.group(1) or "").upper()
        if qualifier != "_INPUT":
            continue
        for raw in m.group(2).split(";"):
            line = re.sub(r"\(\*.*?\*\)", "", raw).strip()
            if not line or ":" not in line:
                continue
            names_part, _, type_part = line.partition(":")
            type_part = type_part.split(":=")[0].strip().rstrip(";").strip()
            type_token = type_part.split()[0] if type_part else ""
            if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*(\(.*\))?$", type_token):
                return None
            lit = default_literal(type_token)
            if lit is None:
                return None
            for _ in names_part.split(","):
                args.append(lit)
    return args


def build_harness(proj, app, specs):
    """Create CI_HARNESS_PRG on MainTask referencing every non-program POU so that
    all of them are compiled. Returns wire warnings."""
    warnings_out = []
    inst_decls = []
    calls = []
    seq = 0
    programs_to_mount = []

    for spec in specs:
        name = spec["name"]
        kind = spec["_kind"]
        if name in (HARNESS, "PLC_PRG"):
            continue
        seq += 1
        if kind == "function_block":
            if has_var_in_out(spec.get("declaration") or ""):
                warnings_out.append(
                    "auto-wire: FUNCTION_BLOCK '%s' not called (VAR_IN_OUT "
                    "signature); its body may not be compile-checked" % name)
                continue
            var = "ci_fb_%d" % seq
            inst_decls.append("    %s : %s;" % (var, name))
            calls.append("%s();" % var)
        elif kind == "function":
            rtype = function_return_type(spec)
            args = function_input_args(spec.get("declaration") or "")
            if args is None:
                warnings_out.append(
                    "auto-wire: FUNCTION '%s' not called (unsupported "
                    "signature); its body is not compile-checked" % name)
                continue
            rvar = "ci_r_%d" % seq
            inst_decls.append("    %s : %s;" % (rvar, rtype))
            calls.append("%s := %s(%s);" % (rvar, name, ", ".join(args)))
        elif kind == "program":
            programs_to_mount.append(name)

    if not inst_decls and not calls and not programs_to_mount:
        return warnings_out

    # mount extra programs directly on the task
    tc = None
    for c in proj.get_children(True):
        if c.is_task_configuration:
            tc = c
            break
    if tc is None:
        tc = app.create_task_configuration()
    task = None
    for c in tc.get_children(False):
        if c.is_task:
            task = c
            break
    if task is None:
        task = tc.create_task("MainTask")
    for pname in programs_to_mount:
        try:
            task.pous.add(pname)
        except Exception, e:
            warnings_out.append("auto-wire: task.pous.add('%s') failed: %s"
                                % (pname, e))

    if not inst_decls:
        return warnings_out

    h_decl = "PROGRAM %s\nVAR\n%s\nEND_VAR\n" % (HARNESS, "\n".join(inst_decls))
    h_impl = "\n".join(calls) + "\n"
    hpou = find_pou(proj, HARNESS)
    if hpou is None:
        hpou = app.create_pou(name=HARNESS, type=PouType.Program, language=None)
    replace_doc(hpou.textual_declaration, h_decl)
    replace_doc(hpou.textual_implementation, h_impl)
    task.pous.add(HARNESS)
    return warnings_out


def create_pou(app, proj, spec):
    name = spec["name"]
    kind = normalize_kind(spec.get("kind"), name)
    spec["_kind"] = kind
    pou = find_pou(proj, name)
    if pou is not None:
        return pou
    if kind == "function":
        rtype = function_return_type(spec)
        return app.create_pou(name=name, type=PouType.Function,
                              return_type=rtype, language=None)
    return app.create_pou(name=name, type=pou_kind_enum(kind), language=None)


DUT_KINDS = {
    "struct": DutType.Structure,
    "structure": DutType.Structure,
    "enum": DutType.Enumeration,
    "enumeration": DutType.Enumeration,
    "alias": DutType.Alias,
    "union": DutType.Union,
}


def normalize_dut_kind(kind):
    k = str(kind).strip().lower() if kind else "struct"
    if k in DUT_KINDS:
        return DUT_KINDS[k]
    raise ValueError("unknown DUT kind: %r" % kind)


def create_dut(app, proj, spec):
    name = spec["name"]
    dut = find_pou(proj, name)
    if dut is not None:
        return dut
    return app.create_dut(name, normalize_dut_kind(spec.get("kind")))


def ensure_standard_library(app):
    """Reference the Standard library so TON/TOF/TP/R_TRIG/F_TRIG/CTU compile.

    A project created through the scripting API does not reference the Standard
    library by default (unlike one created in the CODESYS GUI), so any model code
    using standard timer/trigger function blocks would wrongly fail with
    "unknown type TON". add_placeholder is idempotent for our purposes."""
    try:
        app.get_library_manager().add_placeholder(
            "Standard", "Standard, 3.5.22.0 (3S - Smart Software Solutions GmbH)")
    except Exception:
        pass


def cleanup_project(project_path):
    folder = os.path.dirname(project_path)
    stem = os.path.basename(project_path)
    if stem.lower().endswith(".project"):
        stem = stem[:-len(".project")]
    for fn in os.listdir(folder):
        if fn == stem + ".project":
            continue
        if fn.startswith(stem) and (fn.endswith(".opt")
                                    or fn.endswith(".precompilecache")
                                    or ".simulation." in fn):
            try:
                os.remove(os.path.join(folder, fn))
            except Exception:
                pass


def run_job(job, seq):
    start = ticks()
    jid = job.get("id") if hasattr(job, "get") else None
    result = {
        "id": jid if jid is not None else "job%d" % seq,
        "passed": False,
        "errors": [],
        "warnings": [],
        "info_count": 0,
        "wire_warnings": [],
        "elapsed_ms": 0,
        "fatal": None,
        "project_copy": None,
    }
    project_path = job_project_path(jid)
    proj = None
    try:
        specs = job.get("pous")
        if not specs:
            raise ValueError("job has no 'pous' list")
        duts = job.get("duts") or []
        reserved_names = [s.get("name") for s in specs] + \
                         [s.get("name") for s in duts]
        if HARNESS in reserved_names:
            raise ValueError("name '%s' is reserved" % HARNESS)

        System.IO.File.Copy(TEMPLATE, project_path, True)
        proj = projects.open(project_path, None, True)
        if not proj:
            raise RuntimeError("projects.open returned None")
        app = proj.active_application
        if not app:
            raise RuntimeError("template project has no active application")
        ensure_standard_library(app)

        for spec in duts:
            if not spec.get("name"):
                raise ValueError("a DUT spec is missing 'name'")
            dut = create_dut(app, proj, spec)
            if dut is None:
                dut = find_pou(proj, spec["name"])
            if dut is None:
                raise RuntimeError("could not create DUT '%s'" % spec["name"])
            replace_doc(dut.textual_declaration, spec.get("declaration"))

        for spec in specs:
            if not spec.get("name"):
                raise ValueError("a POU spec is missing 'name'")
            pou = create_pou(app, proj, spec)
            if pou is None:
                pou = find_pou(proj, spec["name"])
            if pou is None:
                raise RuntimeError("could not create POU '%s'" % spec["name"])
            replace_doc(pou.textual_declaration, spec.get("declaration"))
            replace_doc(pou.textual_implementation, spec.get("implementation"))

        if job.get("auto_wire", True):
            result["wire_warnings"] = build_harness(proj, app, specs)

        try:
            system.clear_messages()
        except Exception:
            pass
        app.rebuild()
        system.delay(1500)

        errors, warnings, info_count = collect_diagnostics()
        result["errors"] = errors
        result["warnings"] = warnings
        result["info_count"] = info_count
        result["passed"] = (len(errors) == 0)
    except Exception, e:
        result["fatal"] = "%s: %s" % (type(e).__name__, e)
        result["passed"] = False
    finally:
        if proj is not None:
            try:
                proj.close()
            except Exception:
                pass

    if job.get("keep_project"):
        result["project_copy"] = project_path
    else:
        cleanup_project(project_path)
        try:
            System.IO.File.Delete(project_path)
        except Exception:
            pass

    result["elapsed_ms"] = elapsed_ms(start)
    return result


def main():
    if not REQ or not RESP:
        raise RuntimeError("usage: compile_worker.py <request.json> <response.json>")
    if not System.IO.File.Exists(TEMPLATE):
        raise RuntimeError("template project missing: " + TEMPLATE)

    req = json.loads(System.IO.File.ReadAllText(
        REQ, System.Text.Encoding.UTF8))
    if isinstance(req, dict) and "jobs" in req:
        jobs = req["jobs"]
    elif isinstance(req, list):
        jobs = req
    else:
        jobs = [req]

    results = []
    wall = ticks()
    for seq, job in enumerate(jobs):
        try:
            results.append(run_job(job, seq + 1))
        except Exception, e:
            results.append({
                "id": (job.get("id") if isinstance(job, dict) else None)
                      or ("job%d" % (seq + 1)),
                "passed": False, "errors": [], "warnings": [],
                "info_count": 0, "wire_warnings": [], "elapsed_ms": 0,
                "fatal": "worker: %s: %s" % (type(e).__name__, e),
                "project_copy": None,
            })

    write_json(RESP, {
        "ok": True,
        "results": results,
        "elapsed_ms": elapsed_ms(wall),
        "error": None,
    })


try:
    main()
    rc = 0
except Exception:
    import traceback
    rc = 2
    try:
        if RESP:
            write_json(RESP, {
                "ok": False,
                "results": [],
                "elapsed_ms": 0,
                "error": traceback.format_exc(),
            })
    except Exception:
        pass
terminate(rc)
