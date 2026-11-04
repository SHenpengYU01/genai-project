# Generate the clean template project used by the compile service:
#   fresh project + Control Win V3 x64 device + Application
#   + empty PLC_PRG (PROGRAM, on MainTask)
# The generated template itself builds clean (verified before delivery).
# ASCII-only (IronPython 2.7 PEP 263 parse rule).
import System
import os
from scriptengine import *

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "template.project")
LOG = os.path.join(HERE, "make_template.log")

DEVICE_TYPE = 4096
DEVICE_ID = "0000 0004"
DEVICE_VERSION = "3.5.22.40"

w = System.IO.StreamWriter(LOG)


def log(s):
    w.WriteLine(unicode(s))
    w.Flush()


def terminate(code):
    try:
        w.Flush()
        w.Close()
    except Exception:
        pass

    def kill(state):
        try:
            System.Diagnostics.Process.GetCurrentProcess().Kill()
        except Exception:
            pass

    System.Threading.Timer(
        System.Threading.TimerCallback(kill), None, 3000,
        System.Threading.Timeout.Infinite)
    System.Environment.Exit(code)


def must(cond, msg):
    if not cond:
        log("FATAL: " + msg)
        terminate(1)


def set_text(doc, txt):
    try:
        doc.replace(txt)
        return
    except Exception:
        pass
    doc.text = txt


def main():
    log("creating template: " + TEMPLATE)
    if System.IO.File.Exists(TEMPLATE):
        System.IO.File.Delete(TEMPLATE)

    proj = projects.create(TEMPLATE, True)
    must(proj is not None, "projects.create returned None")

    res = proj.add("Device", DEVICE_TYPE, DEVICE_ID, DEVICE_VERSION)
    log("proj.add device -> %r" % (res,))

    app = proj.active_application
    must(app is not None, "no active application after device add")

    # PLC_PRG program, initially empty
    pou = app.create_program("PLC_PRG")
    if pou is None:
        found = proj.find("PLC_PRG")
        must(bool(found), "create_program returned nothing and PLC_PRG not found")
        pou = found[0]
    set_text(pou.textual_declaration, "PROGRAM PLC_PRG\nVAR\nEND_VAR\n")
    set_text(pou.textual_implementation, "")
    log("PLC_PRG prepared")

    # MainTask calls PLC_PRG
    tc = None
    for c in proj.get_children(True):
        if c.is_task_configuration:
            tc = c
            break
    if tc is None:
        tc = app.create_task_configuration()
    must(tc is not None, "cannot create task configuration")

    task = None
    for c in tc.get_children(False):
        if c.is_task:
            task = c
            break
    if task is None:
        task = tc.create_task("MainTask")
    must(task is not None, "cannot create MainTask")
    task.pous.add("PLC_PRG")
    log("MainTask -> PLC_PRG configured")

    # sanity build: the empty template itself must have 0 errors
    try:
        system.clear_messages()
    except Exception:
        pass
    app.build()
    system.delay(1500)
    n_err = 0
    for cat in system.get_message_categories(True):
        for o in system.get_message_objects(cat.ToString()):
            if int(o.severity) & 3:
                n_err += 1
                log("TEMPLATE ERROR: [%s] %s" % (o.severity, o))
    must(n_err == 0, "template sanity build reported %d error(s)" % n_err)

    proj.save()
    proj.close()
    log("TEMPLATE OK")
    return 0


try:
    rc = main()
except Exception:
    import traceback
    try:
        log("UNHANDLED EXCEPTION:\n" + traceback.format_exc())
    except Exception:
        pass
    rc = 1
terminate(rc)
