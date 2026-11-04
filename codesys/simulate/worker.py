# Stateless single-task simulation worker for CODESYS (IronPython 2.7).
# Invoked by run_simulation.bat from codesys/simulate/runner.py.
#
# Builds the project (DUTs + POU under test + generated self-test driver),
# sets the MainTask cycle time to the test's scan_ms, enables Control Win V3
# simulation, logs in, starts, and polls CI_TEST_DRIVER.done until the test
# sequence finishes, then reports pass/fail counts.
#
# Request JSON (UTF-8):
#   { "id": "...", "scan_ms": 10,
#     "duts": [ ... ], "pous": [ ... ],   # code under test (the FB)
#     "driver": "PROGRAM CI_TEST_DRIVER\nVAR ... END_VAR\n<body>" }
#
# Response JSON:
#   { "ok": true, "id": "...", "allPass": bool, "passCnt": int,
#     "failCnt": int, "firstFailTc": int, "firstFailStep": int,
#     "elapsed_ms": int, "error": null }
import sys
import os
import re
import json
import System
from scriptengine import *

REQ = sys.argv[1] if len(sys.argv) > 1 else None
RESP = sys.argv[2] if len(sys.argv) > 2 else None

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.normpath(os.path.join(HERE, "..", "template.project"))
WORKDIR = os.path.join(HERE, "work")

DUT_KINDS = {
    "struct": DutType.Structure,
    "structure": DutType.Structure,
    "enum": DutType.Enumeration,
    "enumeration": DutType.Enumeration,
    "alias": DutType.Alias,
    "union": DutType.Union,
}


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

    System.Threading.Timer(System.Threading.TimerCallback(kill), None, 3000,
                           System.Threading.Timeout.Infinite)
    System.Environment.Exit(code)


def write_json(path, obj):
    System.IO.File.WriteAllText(
        path, json.dumps(obj, ensure_ascii=False, indent=1),
        System.Text.UTF8Encoding(False))


def replace_doc(doc, text):
    if text is None:
        return
    try:
        doc.replace(text)
        return
    except Exception:
        pass
    doc.text = text


def find_obj(proj, name):
    try:
        for h in (proj.find(name, True) or []):
            try:
                if h.get_name() == name:
                    return h
            except Exception:
                return h
    except Exception:
        pass
    return None


def normalize_kind(kind, name):
    k = str(kind).strip().lower() if kind else ""
    if k in ("program", "prg"):
        return "program"
    if k in ("function", "fun", "func"):
        return "function"
    if k in ("function_block", "functionblock", "fb"):
        return "function_block"
    if k:
        raise ValueError("unknown POU kind: %r" % kind)
    return "program" if name == "PLC_PRG" else "function_block"


def pou_kind_enum(kind):
    return {"program": PouType.Program,
            "function_block": PouType.FunctionBlock,
            "function": PouType.Function}[kind]


def normalize_dut_kind(kind):
    k = str(kind).strip().lower() if kind else "struct"
    if k in DUT_KINDS:
        return DUT_KINDS[k]
    raise ValueError("unknown DUT kind: %r" % kind)


def create_pou(app, proj, spec):
    name = spec["name"]
    kind = normalize_kind(spec.get("kind"), name)
    pou = find_obj(proj, name)
    if pou is not None:
        return pou
    return app.create_pou(name=name, type=pou_kind_enum(kind), language=None)


def create_dut(app, proj, spec):
    name = spec["name"]
    dut = find_obj(proj, name)
    if dut is not None:
        return dut
    return app.create_dut(name, normalize_dut_kind(spec.get("kind")))


def ensure_standard_library(app):
    try:
        app.get_library_manager().add_placeholder(
            "Standard", "Standard, 3.5.22.0 (3S - Smart Software Solutions GmbH)")
    except Exception:
        pass


def main():
    start = ticks()
    resp = {"ok": False, "id": None, "allPass": False, "passCnt": 0,
            "failCnt": 0, "firstFailTc": -1, "firstFailStep": -1,
            "elapsed_ms": 0, "error": None}
    proj = None
    try:
        req = json.loads(System.IO.File.ReadAllText(
            REQ, System.Text.Encoding.UTF8))
        resp["id"] = req.get("id")
        scan_ms = int(req.get("scan_ms", 10))
        if not System.IO.Directory.Exists(WORKDIR):
            System.IO.Directory.CreateDirectory(WORKDIR)
        projpath = os.path.join(WORKDIR, "sim_%d.project" % ticks())
        System.IO.File.Copy(TEMPLATE, projpath, True)
        proj = projects.open(projpath, None, True)
        app = proj.active_application
        ensure_standard_library(app)

        for spec in req.get("duts") or []:
            dut = create_dut(app, proj, spec)
            if dut is None:
                dut = find_obj(proj, spec["name"])
            replace_doc(dut.textual_declaration, spec.get("declaration"))

        for spec in req.get("pous") or []:
            pou = create_pou(app, proj, spec)
            replace_doc(pou.textual_declaration, spec.get("declaration"))
            replace_doc(pou.textual_implementation, spec.get("implementation"))

        # split driver into declaration (through END_VAR) and body
        driver = req["driver"]
        m = re.search(r"END_VAR\b", driver)
        decl = driver[:m.end()].strip() + "\n"
        impl = driver[m.end():].strip() + "\n"
        dpou = app.create_pou(name="CI_TEST_DRIVER", type=PouType.Program,
                              language=None)
        replace_doc(dpou.textual_declaration, decl)
        replace_doc(dpou.textual_implementation, impl)

        # mount driver on MainTask
        tc = None
        for c in proj.get_children(True):
            if c.is_task_configuration:
                tc = c
                break
        task = None
        for c in tc.get_children(False):
            if c.is_task:
                task = c
                break
        task.pous.add("CI_TEST_DRIVER")
        task.interval = "T#%dms" % scan_ms

        try:
            system.clear_messages()
        except Exception:
            pass
        app.rebuild()
        system.delay(1500)
        err_texts = []
        for cat in system.get_message_categories(True):
            for o in system.get_message_objects(cat.ToString()):
                if int(o.severity) & 3:
                    try:
                        loc = getattr(o, "position_text", None) or ""
                        msg = getattr(o, "message", None) or str(o)
                        err_texts.append("%s %s: %s" % (loc, getattr(o, "severity", ""), msg))
                    except Exception:
                        err_texts.append(str(o))
        if err_texts:
            raise RuntimeError("build errors:\n" + "\n".join(err_texts[:40]))

        app.generate_code()

        # enable simulation and login
        device = None
        for c in proj.get_children(True):
            try:
                if hasattr(c, "is_device") and c.is_device:
                    device = c
                    break
            except Exception:
                pass
        device.set_simulation_mode(True)
        oa = online.create_online_application(app)
        oa.login(OnlineChangeOption.Force, False)
        oa.start()

        # poll done
        done = False
        max_iters = 3000  # ~300s at 100ms poll
        it = 0
        while it < max_iters:
            system.delay(100)
            try:
                v = oa.read_value("CI_TEST_DRIVER.done")
                if str(v).upper() == "TRUE":
                    done = True
                    break
            except Exception:
                pass
            it += 1

        if not done:
            raise RuntimeError("test driver did not finish within timeout")

        def rd(sym):
            return str(oa.read_value(sym))

        def as_bool(v):
            return "TRUE" in str(v).upper()

        def as_int(v):
            s = str(v).strip()
            if '#' in s:
                s = s.split('#', 1)[1]
            return int(s)

        resp["allPass"] = as_bool(rd("CI_TEST_DRIVER.allPass"))
        resp["passCnt"] = as_int(rd("CI_TEST_DRIVER.passCnt"))
        resp["failCnt"] = as_int(rd("CI_TEST_DRIVER.failCnt"))
        resp["firstFailTc"] = as_int(rd("CI_TEST_DRIVER.firstFailTc"))
        resp["firstFailStep"] = as_int(rd("CI_TEST_DRIVER.firstFailStep"))
        debug = {}
        for sym in req.get("debug_reads") or []:
            try:
                debug[sym] = rd(sym)
            except Exception, e:
                debug[sym] = "ERR:%s" % e
        resp["debug"] = debug
        resp["ok"] = True

        try:
            oa.stop()
        except Exception:
            pass
        try:
            oa.logout()
        except Exception:
            pass
    except Exception, e:
        import traceback
        resp["error"] = "%s: %s\n%s" % (type(e).__name__, e,
                                        traceback.format_exc())
    finally:
        if proj is not None:
            try:
                proj.close()
            except Exception:
                pass
    resp["elapsed_ms"] = elapsed_ms(start)
    write_json(RESP, resp)


try:
    main()
    rc = 0
except Exception:
    import traceback
    rc = 2
    try:
        write_json(RESP, {"ok": False, "id": None, "allPass": False,
                          "passCnt": 0, "failCnt": 0, "firstFailTc": -1,
                          "firstFailStep": -1, "elapsed_ms": 0,
                          "error": traceback.format_exc()})
    except Exception:
        pass
terminate(rc)
