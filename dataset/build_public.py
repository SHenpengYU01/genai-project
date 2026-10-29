"""Build the public-question task files from the structured dataset.

Each entry in TASKS is a full task dict; running this script writes one
JSON file per task into dataset/tasks/. Reference ST code uses real newlines
(triple-quoted strings) and is serialized to JSON with \\n escapes.

Run:  python dataset/build_public.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tasks")

TASKS = []

# ---------------------------------------------------------------------------
# easy 1: Automated Filling Line Control
# ---------------------------------------------------------------------------
TASKS.append({
    "id": "public_easy_001",
    "source": "public",
    "difficulty": "easy",
    "title": "自动灌装线控制",
    "pou": {"type": "function_block", "name": "FillingLine"},
    "requirement": {
        "en": (
            "An automated filling line cleans, fills, caps and packages bottles. "
            "When bottleSensor detects a bottle, start the cleaning pump and keep it "
            "running. On cleaningConfirmButton, stop the pump and start the filling "
            "valve. On fillingConfirmButton, start the capping machine. On "
            "cappingConfirmButton, start the packing machine. On packingConfirmButton, "
            "turn on the completion light. On finishedButton, reset the light and get "
            "ready for the next bottle."
        ),
        "zh": (
            "自动灌装线负责清洗、灌装、封盖和打包瓶子。当 bottleSensor 检测到瓶子时，"
            "启动清洗泵并持续运行；收到 cleaningConfirmButton 后停止清洗泵并打开灌装阀；"
            "收到 fillingConfirmButton 后启动封盖机；收到 cappingConfirmButton 后启动"
            "打包机；收到 packingConfirmButton 后点亮完成指示灯；收到 finishedButton 后"
            "熄灭指示灯，准备下一个瓶子的生产周期。"
        ),
    },
    "interface": {
        "duts": [],
        "inputs": [
            {"name": "bottleSensor", "type": "BOOL", "desc": "检测到瓶子"},
            {"name": "cleaningConfirmButton", "type": "BOOL", "desc": "清洗完成确认"},
            {"name": "fillingConfirmButton", "type": "BOOL", "desc": "灌装完成确认"},
            {"name": "cappingConfirmButton", "type": "BOOL", "desc": "封盖完成确认"},
            {"name": "packingConfirmButton", "type": "BOOL", "desc": "打包完成确认"},
            {"name": "finishedButton", "type": "BOOL", "desc": "取走完成确认"},
        ],
        "outputs": [
            {"name": "Pump_Motor", "type": "BOOL", "desc": "清洗泵电机"},
            {"name": "Filling_Valve", "type": "BOOL", "desc": "灌装阀"},
            {"name": "Capping_Machine", "type": "BOOL", "desc": "封盖机"},
            {"name": "Packing_Machine", "type": "BOOL", "desc": "打包机"},
            {"name": "Completion_Light", "type": "BOOL", "desc": "完成指示灯"},
        ],
        "inouts": [],
    },
    "ltl_specs": [
        {"id": "P1", "description": "各工位输出互斥（同一时刻至多一个工位激活）。",
         "formula": "G(!(Pump_Motor && Filling_Valve) && !(Filling_Valve && Capping_Machine) && !(Capping_Machine && Packing_Machine) && !(Packing_Machine && Completion_Light))"},
        {"id": "P2", "description": "检测到瓶子后启动清洗泵。",
         "formula": "G(bottleSensor -> X(Pump_Motor))"},
        {"id": "P3", "description": "清洗确认后进入灌装。",
         "formula": "G((Pump_Motor && cleaningConfirmButton) -> X(Filling_Valve))"},
        {"id": "P4", "description": "打包确认后点亮完成指示灯。",
         "formula": "G((Packing_Machine && packingConfirmButton) -> X(Completion_Light))"},
        {"id": "P5", "description": "取走确认后熄灭指示灯并复位。",
         "formula": "G((Completion_Light && finishedButton) -> X(!Completion_Light))"},
    ],
    "test_cases": [
        {"id": "TC1", "description": "完整生产流程顺序推进", "scan_ms": 10, "steps": [
            {"inputs": {"bottleSensor": False, "cleaningConfirmButton": False,
                        "fillingConfirmButton": False, "cappingConfirmButton": False,
                        "packingConfirmButton": False, "finishedButton": False},
             "expect": {}},
            {"inputs": {"bottleSensor": True, "cleaningConfirmButton": False,
                        "fillingConfirmButton": False, "cappingConfirmButton": False,
                        "packingConfirmButton": False, "finishedButton": False},
             "expect": {}},
            {"inputs": {"bottleSensor": False, "cleaningConfirmButton": False,
                        "fillingConfirmButton": False, "cappingConfirmButton": False,
                        "packingConfirmButton": False, "finishedButton": False},
             "expect": {"Pump_Motor": True}},
            {"inputs": {"bottleSensor": False, "cleaningConfirmButton": True,
                        "fillingConfirmButton": False, "cappingConfirmButton": False,
                        "packingConfirmButton": False, "finishedButton": False},
             "expect": {"Pump_Motor": True}},
            {"inputs": {"bottleSensor": False, "cleaningConfirmButton": False,
                        "fillingConfirmButton": False, "cappingConfirmButton": False,
                        "packingConfirmButton": False, "finishedButton": False},
             "expect": {"Filling_Valve": True}},
            {"inputs": {"bottleSensor": False, "cleaningConfirmButton": False,
                        "fillingConfirmButton": True, "cappingConfirmButton": False,
                        "packingConfirmButton": False, "finishedButton": False},
             "expect": {"Filling_Valve": True}},
            {"inputs": {"bottleSensor": False, "cleaningConfirmButton": False,
                        "fillingConfirmButton": False, "cappingConfirmButton": False,
                        "packingConfirmButton": False, "finishedButton": False},
             "expect": {"Capping_Machine": True}},
            {"inputs": {"bottleSensor": False, "cleaningConfirmButton": False,
                        "fillingConfirmButton": False, "cappingConfirmButton": True,
                        "packingConfirmButton": False, "finishedButton": False},
             "expect": {"Capping_Machine": True}},
            {"inputs": {"bottleSensor": False, "cleaningConfirmButton": False,
                        "fillingConfirmButton": False, "cappingConfirmButton": False,
                        "packingConfirmButton": False, "finishedButton": False},
             "expect": {"Packing_Machine": True}},
            {"inputs": {"bottleSensor": False, "cleaningConfirmButton": False,
                        "fillingConfirmButton": False, "cappingConfirmButton": False,
                        "packingConfirmButton": True, "finishedButton": False},
             "expect": {"Packing_Machine": True}},
            {"inputs": {"bottleSensor": False, "cleaningConfirmButton": False,
                        "fillingConfirmButton": False, "cappingConfirmButton": False,
                        "packingConfirmButton": False, "finishedButton": False},
             "expect": {"Completion_Light": True}},
            {"inputs": {"bottleSensor": False, "cleaningConfirmButton": False,
                        "fillingConfirmButton": False, "cappingConfirmButton": False,
                        "packingConfirmButton": False, "finishedButton": True},
             "expect": {"Completion_Light": True}},
            {"inputs": {"bottleSensor": False, "cleaningConfirmButton": False,
                        "fillingConfirmButton": False, "cappingConfirmButton": False,
                        "packingConfirmButton": False, "finishedButton": False},
             "expect": {}},
        ]},
    ],
    "reference": {
        "duts": [],
        "pous": [{
            "name": "FillingLine",
            "kind": "function_block",
            "declaration": (
                "FUNCTION_BLOCK FillingLine\n"
                "VAR_INPUT\n"
                "    bottleSensor : BOOL;\n"
                "    cleaningConfirmButton : BOOL;\n"
                "    fillingConfirmButton : BOOL;\n"
                "    cappingConfirmButton : BOOL;\n"
                "    packingConfirmButton : BOOL;\n"
                "    finishedButton : BOOL;\n"
                "END_VAR\n"
                "VAR_OUTPUT\n"
                "    Pump_Motor : BOOL;\n"
                "    Filling_Valve : BOOL;\n"
                "    Capping_Machine : BOOL;\n"
                "    Packing_Machine : BOOL;\n"
                "    Completion_Light : BOOL;\n"
                "END_VAR\n"
                "VAR\n"
                "    stage : INT := 0;\n"
                "END_VAR\n"),
            "implementation": (
                "Pump_Motor := FALSE;\n"
                "Filling_Valve := FALSE;\n"
                "Capping_Machine := FALSE;\n"
                "Packing_Machine := FALSE;\n"
                "Completion_Light := FALSE;\n"
                "CASE stage OF\n"
                "0:\n"
                "    IF bottleSensor THEN\n"
                "        stage := 1;\n"
                "    END_IF\n"
                "1:\n"
                "    Pump_Motor := TRUE;\n"
                "    IF cleaningConfirmButton THEN\n"
                "        stage := 2;\n"
                "    END_IF\n"
                "2:\n"
                "    Filling_Valve := TRUE;\n"
                "    IF fillingConfirmButton THEN\n"
                "        stage := 3;\n"
                "    END_IF\n"
                "3:\n"
                "    Capping_Machine := TRUE;\n"
                "    IF cappingConfirmButton THEN\n"
                "        stage := 4;\n"
                "    END_IF\n"
                "4:\n"
                "    Packing_Machine := TRUE;\n"
                "    IF packingConfirmButton THEN\n"
                "        stage := 5;\n"
                "    END_IF\n"
                "5:\n"
                "    Completion_Light := TRUE;\n"
                "    IF finishedButton THEN\n"
                "        stage := 0;\n"
                "    END_IF\n"
                "END_CASE\n"),
        }],
    },
})

# ---------------------------------------------------------------------------
# easy 2: Dual-Word Edge Detection
# ---------------------------------------------------------------------------
TASKS.append({
    "id": "public_easy_002",
    "source": "public",
    "difficulty": "easy",
    "title": "双字边沿检测",
    "pou": {"type": "function_block", "name": "EdgeDetect"},
    "requirement": {
        "en": (
            "Write a function block that checks every cycle for rising and falling "
            "edges in each bit of a DWORD input value, and reports changes, rising "
            "edges and falling edges."
        ),
        "zh": (
            "写一个功能块，每个周期检查双字(DWORD)输入 value 的每一位是否出现上升沿或"
            "下降沿，并报告是否有变化、是否有上升沿/下降沿、对应位流及边沿数量。"
        ),
    },
    "interface": {
        "duts": [],
        "inputs": [
            {"name": "value", "type": "DWORD", "desc": "待检测的输入值"},
        ],
        "outputs": [
            {"name": "hasChanged", "type": "BOOL", "desc": "输入值是否发生变化"},
            {"name": "hasRisingEdges", "type": "BOOL", "desc": "是否出现上升沿"},
            {"name": "risingBits", "type": "DWORD", "desc": "上升沿位流"},
            {"name": "noOfRisingBits", "type": "USINT", "desc": "上升沿数量"},
            {"name": "hasFallingEdges", "type": "BOOL", "desc": "是否出现下降沿"},
            {"name": "fallingBits", "type": "DWORD", "desc": "下降沿位流"},
            {"name": "noOfFallingBits", "type": "USINT", "desc": "下降沿数量"},
        ],
        "inouts": [],
    },
    "ltl_specs": [
        {"id": "P1", "description": "只要有变化，就至少有一个上升或下降沿。",
         "formula": "G(hasChanged -> (risingBits <> 0 || fallingBits <> 0))"},
        {"id": "P2", "description": "上升沿标志与上升沿位流一致。",
         "formula": "G((risingBits <> 0) <-> hasRisingEdges)"},
        {"id": "P3", "description": "下降沿标志与下降沿位流一致。",
         "formula": "G((fallingBits <> 0) <-> hasFallingEdges)"},
        {"id": "P4", "description": "同一位不可能同时上升和下降。",
         "formula": "G((risingBits AND fallingBits) = 0)"},
    ],
    "test_cases": [
        {"id": "TC1", "description": "上升沿检测", "scan_ms": 10, "steps": [
            {"inputs": {"value": 0},
             "expect": {"hasChanged": False, "hasRisingEdges": False,
                        "risingBits": 0, "noOfRisingBits": 0,
                        "hasFallingEdges": False, "fallingBits": 0,
                        "noOfFallingBits": 0}},
            {"inputs": {"value": 5},
             "expect": {"hasChanged": True, "hasRisingEdges": True,
                        "risingBits": 5, "noOfRisingBits": 2,
                        "hasFallingEdges": False, "fallingBits": 0,
                        "noOfFallingBits": 0}},
            {"inputs": {"value": 5},
             "expect": {"hasChanged": False, "hasRisingEdges": False,
                        "risingBits": 0, "noOfRisingBits": 0,
                        "hasFallingEdges": False, "fallingBits": 0,
                        "noOfFallingBits": 0}},
        ]},
        {"id": "TC2", "description": "下降沿与混合边沿", "scan_ms": 10, "steps": [
            {"inputs": {"value": 5},
             "expect": {"hasChanged": False, "hasRisingEdges": False,
                        "risingBits": 0, "noOfRisingBits": 0,
                        "hasFallingEdges": False, "fallingBits": 0,
                        "noOfFallingBits": 0}},
            {"inputs": {"value": 1},
             "expect": {"hasChanged": True, "hasRisingEdges": False,
                        "risingBits": 0, "noOfRisingBits": 0,
                        "hasFallingEdges": True, "fallingBits": 4,
                        "noOfFallingBits": 1}},
        ]},
    ],
    "reference": {
        "duts": [],
        "pous": [{
            "name": "EdgeDetect",
            "kind": "function_block",
            "declaration": (
                "FUNCTION_BLOCK EdgeDetect\n"
                "VAR_INPUT\n"
                "    value : DWORD;\n"
                "END_VAR\n"
                "VAR_OUTPUT\n"
                "    hasChanged : BOOL;\n"
                "    hasRisingEdges : BOOL;\n"
                "    risingBits : DWORD;\n"
                "    noOfRisingBits : USINT;\n"
                "    hasFallingEdges : BOOL;\n"
                "    fallingBits : DWORD;\n"
                "    noOfFallingBits : USINT;\n"
                "END_VAR\n"
                "VAR\n"
                "    prev : DWORD;\n"
                "    i : INT;\n"
                "    mask : DWORD;\n"
                "END_VAR\n"),
            "implementation": (
                "risingBits := 0;\n"
                "fallingBits := 0;\n"
                "noOfRisingBits := 0;\n"
                "noOfFallingBits := 0;\n"
                "hasRisingEdges := FALSE;\n"
                "hasFallingEdges := FALSE;\n"
                "FOR i := 0 TO 31 DO\n"
                "    mask := SHL(DWORD#1, i);\n"
                "    IF ((value AND mask) <> 0) AND ((prev AND mask) = 0) THEN\n"
                "        risingBits := risingBits OR mask;\n"
                "        noOfRisingBits := noOfRisingBits + 1;\n"
                "        hasRisingEdges := TRUE;\n"
                "    ELSIF ((value AND mask) = 0) AND ((prev AND mask) <> 0) THEN\n"
                "        fallingBits := fallingBits OR mask;\n"
                "        noOfFallingBits := noOfFallingBits + 1;\n"
                "        hasFallingEdges := TRUE;\n"
                "    END_IF\n"
                "END_FOR\n"
                "hasChanged := (value <> prev);\n"
                "prev := value;\n"),
        }],
    },
})

# ---------------------------------------------------------------------------
# easy 3: Alarm Handling (hysteresis)
# ---------------------------------------------------------------------------
TASKS.append({
    "id": "public_easy_003",
    "source": "public",
    "difficulty": "easy",
    "title": "带滞环的报警处理",
    "pou": {"type": "function_block", "name": "AlarmHyst"},
    "requirement": {
        "en": (
            "Implement an alarm with hysteresis. When Value > hiLevel trigger hiAlarm; "
            "when Value < hiLevel-hystWindow exit hiAlarm. When Value < loLevel trigger "
            "loAlarm; when Value > loLevel+hystWindow exit loAlarm. If loLevel >= hiLevel "
            "output error=true status=16#8001 and exit. If hystWindow >= hiLevel-loLevel "
            "output error=true status=16#8002."
        ),
        "zh": (
            "实现带滞环的报警：当 Value>hiLevel 时触发高报警 hiAlarm，当 Value<hiLevel-hystWindow "
            "时退出高报警；当 Value<loLevel 时触发低报警 loAlarm，当 Value>loLevel+hystWindow "
            "时退出低报警。若 loLevel>=hiLevel 则输出 error=true、status=16#8001 并退出；"
            "若 hystWindow>=hiLevel-loLevel 则输出 error=true、status=16#8002。"
        ),
    },
    "interface": {
        "duts": [],
        "inputs": [
            {"name": "Value", "type": "REAL", "desc": "输入值"},
            {"name": "hiLevel", "type": "REAL", "desc": "高报警限"},
            {"name": "loLevel", "type": "REAL", "desc": "低报警限"},
            {"name": "hystWindow", "type": "REAL", "desc": "滞环窗口"},
        ],
        "outputs": [
            {"name": "hiAlarm", "type": "BOOL", "desc": "高报警"},
            {"name": "loAlarm", "type": "BOOL", "desc": "低报警"},
            {"name": "error", "type": "BOOL", "desc": "配置错误"},
            {"name": "status", "type": "WORD", "desc": "状态码"},
        ],
        "inouts": [],
    },
    "ltl_specs": [
        {"id": "P1", "description": "超上限触发高报警。",
         "formula": "G((!error && Value > hiLevel) -> hiAlarm)"},
        {"id": "P2", "description": "低于回差下限退出高报警。",
         "formula": "G((!error && Value < hiLevel - hystWindow) -> !hiAlarm)"},
        {"id": "P3", "description": "低于下限触发低报警。",
         "formula": "G((!error && Value < loLevel) -> loAlarm)"},
        {"id": "P4", "description": "高于回差上限退出低报警。",
         "formula": "G((!error && Value > loLevel + hystWindow) -> !loAlarm)"},
        {"id": "P5", "description": "上下限颠倒时报配置错误。",
         "formula": "G((loLevel >= hiLevel) -> error)"},
    ],
    "test_cases": [
        {"id": "TC1", "description": "高报警触发与滞环保持", "scan_ms": 10, "steps": [
            {"inputs": {"Value": 50.0, "hiLevel": 80.0, "loLevel": 20.0, "hystWindow": 5.0},
             "expect": {"hiAlarm": False, "loAlarm": False, "error": False}},
            {"inputs": {"Value": 85.0, "hiLevel": 80.0, "loLevel": 20.0, "hystWindow": 5.0},
             "expect": {"hiAlarm": True}},
            {"inputs": {"Value": 82.0, "hiLevel": 80.0, "loLevel": 20.0, "hystWindow": 5.0},
             "expect": {"hiAlarm": True}},
            {"inputs": {"Value": 74.0, "hiLevel": 80.0, "loLevel": 20.0, "hystWindow": 5.0},
             "expect": {"hiAlarm": False}},
        ]},
        {"id": "TC2", "description": "低报警触发与滞环保持", "scan_ms": 10, "steps": [
            {"inputs": {"Value": 15.0, "hiLevel": 80.0, "loLevel": 20.0, "hystWindow": 5.0},
             "expect": {"loAlarm": True}},
            {"inputs": {"Value": 24.0, "hiLevel": 80.0, "loLevel": 20.0, "hystWindow": 5.0},
             "expect": {"loAlarm": True}},
            {"inputs": {"Value": 26.0, "hiLevel": 80.0, "loLevel": 20.0, "hystWindow": 5.0},
             "expect": {"loAlarm": False}},
        ]},
        {"id": "TC3", "description": "配置错误", "scan_ms": 10, "steps": [
            {"inputs": {"Value": 50.0, "hiLevel": 50.0, "loLevel": 60.0, "hystWindow": 5.0},
             "expect": {"error": True, "status": 32769, "hiAlarm": False, "loAlarm": False}},
            {"inputs": {"Value": 50.0, "hiLevel": 80.0, "loLevel": 20.0, "hystWindow": 70.0},
             "expect": {"error": True, "status": 32770, "hiAlarm": False, "loAlarm": False}},
        ]},
    ],
    "reference": {
        "duts": [],
        "pous": [{
            "name": "AlarmHyst",
            "kind": "function_block",
            "declaration": (
                "FUNCTION_BLOCK AlarmHyst\n"
                "VAR_INPUT\n"
                "    Value : REAL;\n"
                "    hiLevel : REAL;\n"
                "    loLevel : REAL;\n"
                "    hystWindow : REAL;\n"
                "END_VAR\n"
                "VAR_OUTPUT\n"
                "    hiAlarm : BOOL;\n"
                "    loAlarm : BOOL;\n"
                "    error : BOOL;\n"
                "    status : WORD;\n"
                "END_VAR\n"),
            "implementation": (
                "error := FALSE;\n"
                "status := 0;\n"
                "IF loLevel >= hiLevel THEN\n"
                "    error := TRUE;\n"
                "    status := 16#8001;\n"
                "    hiAlarm := FALSE;\n"
                "    loAlarm := FALSE;\n"
                "    RETURN;\n"
                "END_IF\n"
                "IF hystWindow >= (hiLevel - loLevel) THEN\n"
                "    error := TRUE;\n"
                "    status := 16#8002;\n"
                "    hiAlarm := FALSE;\n"
                "    loAlarm := FALSE;\n"
                "    RETURN;\n"
                "END_IF\n"
                "IF Value > hiLevel THEN\n"
                "    hiAlarm := TRUE;\n"
                "ELSIF Value < (hiLevel - hystWindow) THEN\n"
                "    hiAlarm := FALSE;\n"
                "END_IF\n"
                "IF Value < loLevel THEN\n"
                "    loAlarm := TRUE;\n"
                "ELSIF Value > (loLevel + hystWindow) THEN\n"
                "    loAlarm := FALSE;\n"
                "END_IF\n"),
        }],
    },
})

# ---------------------------------------------------------------------------
# easy 4: Jam Pump Debouncing and Runtime Maintenance
# ---------------------------------------------------------------------------
TASKS.append({
    "id": "public_easy_004",
    "source": "public",
    "difficulty": "easy",
    "title": "果酱泵去抖与运行维护",
    "pou": {"type": "function_block", "name": "JamPump"},
    "requirement": {
        "en": (
            "Control a jam transfer pump: debounce VISCOSITY_OK for DebounceTime before "
            "accepting it; allow VFD_RUN only when PASTE_E_STOP_NC and the debounced "
            "viscosity condition hold; e-stop immediately disables the run output and "
            "clears incomplete debounce; accumulate PUMP_RUNTIME_ACC by CycleTime only "
            "while VFD_RUN; set PUMP_MAINT_DUE when runtime reaches 500 hours; initialize "
            "run off, runtime zero and maintenance false at power-up."
        ),
        "zh": (
            "控制果酱输送泵：VISCOSITY_OK 需保持 DebounceTime 时长后才视为有效，失粘立即失效；"
            "仅当 PASTE_E_STOP_NC 为 TRUE 且粘度有效时允许 VFD_RUN；急停立即关断运行并清除"
            "未完成的去抖计时；仅在 VFD_RUN 为 TRUE 时按 CycleTime 累加 PUMP_RUNTIME_ACC；"
            "累计到 500 小时时置位 PUMP_MAINT_DUE；上电时运行关断、累计清零、维护指示为 FALSE。"
        ),
    },
    "interface": {
        "duts": [],
        "inputs": [
            {"name": "VISCOSITY_OK", "type": "BOOL", "desc": "粘度正常原始信号"},
            {"name": "PASTE_E_STOP_NC", "type": "BOOL", "desc": "常闭急停，TRUE 允许运行"},
            {"name": "DebounceTime", "type": "TIME", "desc": "去抖时长"},
            {"name": "CycleTime", "type": "TIME", "desc": "本次调用的实际时间间隔"},
        ],
        "outputs": [
            {"name": "VFD_RUN", "type": "BOOL", "desc": "泵运行命令"},
            {"name": "PUMP_MAINT_DUE", "type": "BOOL", "desc": "维护到期指示"},
            {"name": "PUMP_RUNTIME_ACC", "type": "LTIME", "desc": "累计运行时间"},
        ],
        "inouts": [],
    },
    "ltl_specs": [
        {"id": "P1", "description": "急停优先：急停时必须停止。",
         "formula": "G(!PASTE_E_STOP_NC -> !VFD_RUN)"},
        {"id": "P2", "description": "失粘后立即停止。",
         "formula": "G(!VISCOSITY_OK -> X(!VFD_RUN))"},
        {"id": "P3", "description": "累计运行时间单调不减。",
         "formula": "G(PUMP_RUNTIME_ACC <= X(PUMP_RUNTIME_ACC))"},
    ],
    "test_cases": [
        {"id": "TC1", "description": "去抖后启动并累计运行时间", "scan_ms": 10, "steps": [
            {"inputs": {"VISCOSITY_OK": False, "PASTE_E_STOP_NC": True,
                        "DebounceTime": "T#50ms", "CycleTime": "T#10ms"},
             "expect": {"VFD_RUN": False, "PUMP_RUNTIME_ACC": "T#0ms"}},
            {"inputs": {"VISCOSITY_OK": True, "PASTE_E_STOP_NC": True,
                        "DebounceTime": "T#50ms", "CycleTime": "T#10ms"},
             "expect": {"VFD_RUN": False, "PUMP_RUNTIME_ACC": "T#0ms"}},
            {"inputs": {"VISCOSITY_OK": True, "PASTE_E_STOP_NC": True,
                        "DebounceTime": "T#50ms", "CycleTime": "T#10ms"},
             "expect": {"VFD_RUN": False, "PUMP_RUNTIME_ACC": "T#0ms"}},
            {"inputs": {"VISCOSITY_OK": True, "PASTE_E_STOP_NC": True,
                        "DebounceTime": "T#50ms", "CycleTime": "T#10ms"},
             "expect": {"VFD_RUN": False, "PUMP_RUNTIME_ACC": "T#0ms"}},
            {"inputs": {"VISCOSITY_OK": True, "PASTE_E_STOP_NC": True,
                        "DebounceTime": "T#50ms", "CycleTime": "T#10ms"},
             "expect": {"VFD_RUN": False, "PUMP_RUNTIME_ACC": "T#0ms"}},
            {"inputs": {"VISCOSITY_OK": True, "PASTE_E_STOP_NC": True,
                        "DebounceTime": "T#50ms", "CycleTime": "T#10ms"},
             "expect": {"VFD_RUN": True, "PUMP_RUNTIME_ACC": "T#10ms"}},
            {"inputs": {"VISCOSITY_OK": True, "PASTE_E_STOP_NC": True,
                        "DebounceTime": "T#50ms", "CycleTime": "T#10ms"},
             "expect": {"VFD_RUN": True, "PUMP_RUNTIME_ACC": "T#20ms"}},
        ]},
        {"id": "TC2", "description": "失粘立即停止且累计保持", "scan_ms": 10, "steps": [
            {"inputs": {"VISCOSITY_OK": True, "PASTE_E_STOP_NC": True,
                        "DebounceTime": "T#50ms", "CycleTime": "T#10ms"},
             "expect": {"VFD_RUN": False, "PUMP_RUNTIME_ACC": "T#0ms"}},
            {"inputs": {"VISCOSITY_OK": True, "PASTE_E_STOP_NC": True,
                        "DebounceTime": "T#50ms", "CycleTime": "T#10ms"},
             "expect": {"VFD_RUN": False, "PUMP_RUNTIME_ACC": "T#0ms"}},
            {"inputs": {"VISCOSITY_OK": True, "PASTE_E_STOP_NC": True,
                        "DebounceTime": "T#50ms", "CycleTime": "T#10ms"},
             "expect": {"VFD_RUN": False, "PUMP_RUNTIME_ACC": "T#0ms"}},
            {"inputs": {"VISCOSITY_OK": True, "PASTE_E_STOP_NC": True,
                        "DebounceTime": "T#50ms", "CycleTime": "T#10ms"},
             "expect": {"VFD_RUN": False, "PUMP_RUNTIME_ACC": "T#0ms"}},
            {"inputs": {"VISCOSITY_OK": True, "PASTE_E_STOP_NC": True,
                        "DebounceTime": "T#50ms", "CycleTime": "T#10ms"},
             "expect": {"VFD_RUN": False, "PUMP_RUNTIME_ACC": "T#0ms"}},
            {"inputs": {"VISCOSITY_OK": True, "PASTE_E_STOP_NC": True,
                        "DebounceTime": "T#50ms", "CycleTime": "T#10ms"},
             "expect": {"VFD_RUN": True, "PUMP_RUNTIME_ACC": "T#10ms"}},
            {"inputs": {"VISCOSITY_OK": False, "PASTE_E_STOP_NC": True,
                        "DebounceTime": "T#50ms", "CycleTime": "T#10ms"},
             "expect": {"VFD_RUN": False, "PUMP_RUNTIME_ACC": "T#10ms"}},
        ]},
        {"id": "TC3", "description": "维护到期指示", "scan_ms": 10, "steps": [
            {"inputs": {"VISCOSITY_OK": True, "PASTE_E_STOP_NC": True,
                        "DebounceTime": "T#50ms", "CycleTime": "T#500h"},
             "expect": {"VFD_RUN": True, "PUMP_RUNTIME_ACC": "T#500h",
                        "PUMP_MAINT_DUE": True}},
        ]},
    ],
    "reference": {
        "duts": [],
        "pous": [{
            "name": "JamPump",
            "kind": "function_block",
            "declaration": (
                "FUNCTION_BLOCK JamPump\n"
                "VAR_INPUT\n"
                "    VISCOSITY_OK : BOOL;\n"
                "    PASTE_E_STOP_NC : BOOL;\n"
                "    DebounceTime : TIME;\n"
                "    CycleTime : TIME;\n"
                "END_VAR\n"
                "VAR_OUTPUT\n"
                "    VFD_RUN : BOOL;\n"
                "    PUMP_MAINT_DUE : BOOL;\n"
                "    PUMP_RUNTIME_ACC : LTIME;\n"
                "END_VAR\n"
                "VAR\n"
                "    debounceElapsed : LTIME := LTIME#0ms;\n"
                "    viscValid : BOOL;\n"
                "END_VAR\n"),
            "implementation": (
                "IF NOT VISCOSITY_OK THEN\n"
                "    viscValid := FALSE;\n"
                "    debounceElapsed := LTIME#0ms;\n"
                "ELSIF NOT PASTE_E_STOP_NC THEN\n"
                "    viscValid := FALSE;\n"
                "    debounceElapsed := LTIME#0ms;\n"
                "ELSIF NOT viscValid THEN\n"
                "    debounceElapsed := debounceElapsed + TO_LTIME(CycleTime);\n"
                "    IF debounceElapsed >= TO_LTIME(DebounceTime) THEN\n"
                "        viscValid := TRUE;\n"
                "    END_IF\n"
                "END_IF\n"
                "IF PASTE_E_STOP_NC AND viscValid THEN\n"
                "    VFD_RUN := TRUE;\n"
                "ELSE\n"
                "    VFD_RUN := FALSE;\n"
                "END_IF\n"
                "IF VFD_RUN THEN\n"
                "    PUMP_RUNTIME_ACC := PUMP_RUNTIME_ACC + TO_LTIME(CycleTime);\n"
                "END_IF\n"
                "IF PUMP_RUNTIME_ACC >= TO_LTIME(T#500h) THEN\n"
                "    PUMP_MAINT_DUE := TRUE;\n"
                "END_IF\n"),
        }],
    },
})

# ---------------------------------------------------------------------------
# easy 5: Weld Gap Alarm and Startup Inhibition
# ---------------------------------------------------------------------------
TASKS.append({
    "id": "public_easy_005",
    "source": "public",
    "difficulty": "easy",
    "title": "焊缝间隙报警与启动抑制",
    "pou": {"type": "function_block", "name": "WeldGap"},
    "requirement": {
        "en": (
            "Control a weld-gap alarm: power-up 5-second initialization inhibition "
            "(Operator_Alert FALSE, Weld_Soft_Start_Active TRUE, no debounce accumulation); "
            "after init, alarm only after Gap_Exceeded stays TRUE for DebounceTime; "
            "signal FALSE switches off the alarm and clears debounce; e-stop priority "
            "immediately clears Operator_Alert and debounce."
        ),
        "zh": (
            "控制焊缝间隙报警：上电后有 5 秒初始化抑制期（Operator_Alert 为 FALSE、"
            "Weld_Soft_Start_Active 为 TRUE、间隙去抖不累计）；初始化后仅当 Gap_Exceeded "
            "持续 DebounceTime 后才报警，信号变 FALSE 立即关断报警并清除去抖；急停优先，"
            "立即关断 Operator_Alert 并清除去抖计时。"
        ),
    },
    "interface": {
        "duts": [],
        "inputs": [
            {"name": "Gap_Exceeded", "type": "BOOL", "desc": "间隙超限信号"},
            {"name": "Weld_E_Stop_NC", "type": "BOOL", "desc": "常闭急停，TRUE 表示未触发"},
            {"name": "DebounceTime", "type": "TIME", "desc": "去抖时长"},
        ],
        "outputs": [
            {"name": "Operator_Alert", "type": "BOOL", "desc": "声光报警命令"},
            {"name": "Weld_Soft_Start_Active", "type": "BOOL", "desc": "上电抑制状态"},
        ],
        "inouts": [],
    },
    "ltl_specs": [
        {"id": "P1", "description": "急停优先：急停时不允许报警。",
         "formula": "G(!Weld_E_Stop_NC -> !Operator_Alert)"},
        {"id": "P2", "description": "初始化抑制期不报警。",
         "formula": "G(Weld_Soft_Start_Active -> !Operator_Alert)"},
        {"id": "P3", "description": "报警意味着间隙当前超限。",
         "formula": "G(Operator_Alert -> Gap_Exceeded)"},
        {"id": "P4", "description": "初始化抑制期最终会结束。",
         "formula": "G(F(!Weld_Soft_Start_Active))"},
    ],
    "test_cases": [
        {"id": "TC1", "description": "初始化抑制期后去抖报警并复位", "scan_ms": 20, "steps": [
            {"inputs": {"Gap_Exceeded": True, "Weld_E_Stop_NC": True, "DebounceTime": "T#100ms"},
             "repeat": 100, "expect": {"Weld_Soft_Start_Active": True, "Operator_Alert": False}},
            {"inputs": {"Gap_Exceeded": True, "Weld_E_Stop_NC": True, "DebounceTime": "T#100ms"},
             "repeat": 150, "expect": {"Weld_Soft_Start_Active": False, "Operator_Alert": False}},
            {"inputs": {"Gap_Exceeded": True, "Weld_E_Stop_NC": True, "DebounceTime": "T#100ms"},
             "repeat": 5, "expect": {"Operator_Alert": True}},
            {"inputs": {"Gap_Exceeded": False, "Weld_E_Stop_NC": True, "DebounceTime": "T#100ms"},
             "repeat": 1, "expect": {"Operator_Alert": False}},
        ]},
        {"id": "TC2", "description": "急停优先于初始化和正常监控", "scan_ms": 20, "steps": [
            {"inputs": {"Gap_Exceeded": True, "Weld_E_Stop_NC": False, "DebounceTime": "T#100ms"},
             "repeat": 1, "expect": {"Weld_Soft_Start_Active": True, "Operator_Alert": False}},
        ]},
    ],
    "reference": {
        "duts": [],
        "pous": [{
            "name": "WeldGap",
            "kind": "function_block",
            "declaration": (
                "FUNCTION_BLOCK WeldGap\n"
                "VAR_INPUT\n"
                "    Gap_Exceeded : BOOL;\n"
                "    Weld_E_Stop_NC : BOOL;\n"
                "    DebounceTime : TIME;\n"
                "END_VAR\n"
                "VAR_OUTPUT\n"
                "    Operator_Alert : BOOL;\n"
                "    Weld_Soft_Start_Active : BOOL;\n"
                "END_VAR\n"
                "VAR\n"
                "    initTon : TON;\n"
                "    debounceTon : TON;\n"
                "END_VAR\n"),
            "implementation": (
                "initTon(IN := TRUE, PT := T#5s);\n"
                "Weld_Soft_Start_Active := NOT initTon.Q;\n"
                "IF NOT Weld_E_Stop_NC THEN\n"
                "    Operator_Alert := FALSE;\n"
                "    debounceTon(IN := FALSE, PT := DebounceTime);\n"
                "ELSIF initTon.Q THEN\n"
                "    debounceTon(IN := Gap_Exceeded, PT := DebounceTime);\n"
                "    Operator_Alert := debounceTon.Q;\n"
                "ELSE\n"
                "    Operator_Alert := FALSE;\n"
                "    debounceTon(IN := FALSE, PT := DebounceTime);\n"
                "END_IF\n"),
        }],
    },
})

# ---------------------------------------------------------------------------
# easy 6: Aeration Blower Delayed Start
# ---------------------------------------------------------------------------
TASKS.append({
    "id": "public_easy_006",
    "source": "public",
    "difficulty": "easy",
    "title": "曝气风机延时启动",
    "pou": {"type": "function_block", "name": "AerationBlower"},
    "requirement": {
        "en": (
            "Control an aeration blower: start timing when DO_LOW and AERATION_E_STOP_NC "
            "are both TRUE; BLOWER_RUN only after these conditions hold for 5 seconds; "
            "if DO_LOW goes FALSE or an e-stop occurs, disable BLOWER_RUN and reset the "
            "timer; increment AERATION_BLOWER_CYCLE_COUNT on each FALSE-to-TRUE of "
            "BLOWER_RUN; initialize blower off and count zero."
        ),
        "zh": (
            "控制曝气风机：当 DO_LOW 与 AERATION_E_STOP_NC 均为 TRUE 时开始计时，条件持续 "
            "满足 5 秒后才允许 BLOWER_RUN；若 DO_LOW 变 FALSE 或急停，立即关断 BLOWER_RUN "
            "并复位计时器；在 BLOWER_RUN 每次由 FALSE 变 TRUE 时对 AERATION_BLOWER_CYCLE_COUNT "
            "加 1；上电时风机关断、计数为 0。"
        ),
    },
    "interface": {
        "duts": [],
        "inputs": [
            {"name": "DO_LOW", "type": "BOOL", "desc": "溶解氧低于阈值需曝气"},
            {"name": "AERATION_E_STOP_NC", "type": "BOOL", "desc": "常闭急停，TRUE 未触发"},
        ],
        "outputs": [
            {"name": "BLOWER_RUN", "type": "BOOL", "desc": "风机运行命令"},
            {"name": "AERATION_BLOWER_CYCLE_COUNT", "type": "UINT", "desc": "实际启动次数"},
        ],
        "inouts": [],
    },
    "ltl_specs": [
        {"id": "P1", "description": "急停优先：急停时风机必须停止。",
         "formula": "G(!AERATION_E_STOP_NC -> !BLOWER_RUN)"},
        {"id": "P2", "description": "无需求时风机不运行。",
         "formula": "G(BLOWER_RUN -> DO_LOW)"},
        {"id": "P3", "description": "启动计数单调不减。",
         "formula": "G(AERATION_BLOWER_CYCLE_COUNT <= X(AERATION_BLOWER_CYCLE_COUNT))"},
    ],
    "test_cases": [
        {"id": "TC1", "description": "5 秒延时启动与计数", "scan_ms": 1000, "steps": [
            {"inputs": {"DO_LOW": True, "AERATION_E_STOP_NC": True},
             "expect": {"BLOWER_RUN": False, "AERATION_BLOWER_CYCLE_COUNT": 0}},
            {"inputs": {"DO_LOW": True, "AERATION_E_STOP_NC": True},
             "expect": {"BLOWER_RUN": False, "AERATION_BLOWER_CYCLE_COUNT": 0}},
            {"inputs": {"DO_LOW": True, "AERATION_E_STOP_NC": True},
             "expect": {"BLOWER_RUN": False, "AERATION_BLOWER_CYCLE_COUNT": 0}},
            {"inputs": {"DO_LOW": True, "AERATION_E_STOP_NC": True},
             "expect": {"BLOWER_RUN": False, "AERATION_BLOWER_CYCLE_COUNT": 0}},
            {"inputs": {"DO_LOW": True, "AERATION_E_STOP_NC": True},
             "expect": {"BLOWER_RUN": True, "AERATION_BLOWER_CYCLE_COUNT": 1}},
            {"inputs": {"DO_LOW": True, "AERATION_E_STOP_NC": True},
             "expect": {"BLOWER_RUN": True, "AERATION_BLOWER_CYCLE_COUNT": 1}},
        ]},
        {"id": "TC2", "description": "需求消失复位计时并重新计数", "scan_ms": 1000, "steps": [
            {"inputs": {"DO_LOW": True, "AERATION_E_STOP_NC": True},
             "expect": {"BLOWER_RUN": False, "AERATION_BLOWER_CYCLE_COUNT": 0}},
            {"inputs": {"DO_LOW": True, "AERATION_E_STOP_NC": True},
             "expect": {"BLOWER_RUN": False, "AERATION_BLOWER_CYCLE_COUNT": 0}},
            {"inputs": {"DO_LOW": True, "AERATION_E_STOP_NC": True},
             "expect": {"BLOWER_RUN": False, "AERATION_BLOWER_CYCLE_COUNT": 0}},
            {"inputs": {"DO_LOW": True, "AERATION_E_STOP_NC": True},
             "expect": {"BLOWER_RUN": False, "AERATION_BLOWER_CYCLE_COUNT": 0}},
            {"inputs": {"DO_LOW": True, "AERATION_E_STOP_NC": True},
             "expect": {"BLOWER_RUN": True, "AERATION_BLOWER_CYCLE_COUNT": 1}},
            {"inputs": {"DO_LOW": False, "AERATION_E_STOP_NC": True},
             "expect": {"BLOWER_RUN": False, "AERATION_BLOWER_CYCLE_COUNT": 1}},
            {"inputs": {"DO_LOW": True, "AERATION_E_STOP_NC": True},
             "expect": {"BLOWER_RUN": False, "AERATION_BLOWER_CYCLE_COUNT": 1}},
        ]},
    ],
    "reference": {
        "duts": [],
        "pous": [{
            "name": "AerationBlower",
            "kind": "function_block",
            "declaration": (
                "FUNCTION_BLOCK AerationBlower\n"
                "VAR_INPUT\n"
                "    DO_LOW : BOOL;\n"
                "    AERATION_E_STOP_NC : BOOL;\n"
                "END_VAR\n"
                "VAR_OUTPUT\n"
                "    BLOWER_RUN : BOOL;\n"
                "    AERATION_BLOWER_CYCLE_COUNT : UINT;\n"
                "END_VAR\n"
                "VAR\n"
                "    startTon : TON;\n"
                "    runTrig : R_TRIG;\n"
                "END_VAR\n"),
            "implementation": (
                "startTon(IN := DO_LOW AND AERATION_E_STOP_NC, PT := T#5s);\n"
                "BLOWER_RUN := startTon.Q;\n"
                "runTrig(CLK := BLOWER_RUN);\n"
                "IF runTrig.Q THEN\n"
                "    AERATION_BLOWER_CYCLE_COUNT := AERATION_BLOWER_CYCLE_COUNT + 1;\n"
                "END_IF\n"),
        }],
    },
})


# ---------------------------------------------------------------------------
# medium 1: Multi-Pump Switching Control (struct + VAR_IN_OUT + caller)
# ---------------------------------------------------------------------------
TASKS.append({
    "id": "public_medium_001",
    "source": "public",
    "difficulty": "medium",
    "title": "多泵轮换供水控制",
    "pou": {"type": "function_block", "name": "MultiPump"},
    "requirement": {
        "en": (
            "A water-supply system has 5 pumps. mode selects manual (FALSE) or "
            "automatic (TRUE). In manual mode each pump's RunComd follows its "
            "selection. In automatic mode compare priorities and select the 3 "
            "highest-priority pumps (three in use, two on standby). start starts the "
            "selected pumps, stop stops all pumps."
        ),
        "zh": (
            "供水系统有 5 台泵。mode 选择手动(FALSE)或自动(TRUE)。手动模式下每台泵的 "
            "RunComd 跟随其 selection；自动模式下比较优先级，按'三用二备'自动选出 3 台"
            "优先级更高的泵供水。start 启动所选泵，stop 停止所有泵。"
        ),
    },
    "interface": {
        "duts": [
            {"name": "ST_Pump", "kind": "struct", "fields": [
                {"name": "priority", "type": "INT", "desc": "优先级，越大越高"},
                {"name": "selection", "type": "BOOL", "desc": "手动选中状态"},
                {"name": "RunComd", "type": "BOOL", "desc": "运行命令"},
            ]},
        ],
        "inputs": [
            {"name": "mode", "type": "BOOL", "desc": "FALSE 手动 TRUE 自动"},
            {"name": "start", "type": "BOOL", "desc": "启动所选泵"},
            {"name": "stop", "type": "BOOL", "desc": "停止所有泵"},
        ],
        "outputs": [],
        "inouts": [
            {"name": "pumpGroup", "type": "ARRAY[1..5] OF ST_Pump",
             "desc": "5 台泵记录，读 priority/selection，写 RunComd"},
        ],
    },
    "ltl_specs": [
        {"id": "P1", "description": "停止优先：stop 时所有泵停止。",
         "formula": "G(stop -> !pumpGroup[1].RunComd)"},
        {"id": "P2", "description": "手动：选中的泵在 start 时运行。",
         "formula": "G((!mode && !stop && start && pumpGroup[1].selection) -> pumpGroup[1].RunComd)"},
        {"id": "P3", "description": "手动：未选中的泵不运行。",
         "formula": "G((!mode && !stop && start && !pumpGroup[1].selection) -> !pumpGroup[1].RunComd)"},
    ],
    "test_cases": [
        {"id": "TC1", "description": "手动模式选中泵运行", "scan_ms": 10, "steps": [
            {"inputs": {"mode": False, "start": False, "stop": False,
                        "pumpGroup": [
                            {"priority": 5, "selection": True},
                            {"priority": 1, "selection": False},
                            {"priority": 4, "selection": True},
                            {"priority": 2, "selection": False},
                            {"priority": 3, "selection": False}]},
             "expect": {"pumpGroup": [{"RunComd": False}, {"RunComd": False},
                                      {"RunComd": False}, {"RunComd": False},
                                      {"RunComd": False}]}},
            {"inputs": {"mode": False, "start": True, "stop": False,
                        "pumpGroup": [
                            {"priority": 5, "selection": True},
                            {"priority": 1, "selection": False},
                            {"priority": 4, "selection": True},
                            {"priority": 2, "selection": False},
                            {"priority": 3, "selection": False}]},
             "expect": {"pumpGroup": [{"RunComd": True}, {"RunComd": False},
                                      {"RunComd": True}, {"RunComd": False},
                                      {"RunComd": False}]}},
        ]},
        {"id": "TC2", "description": "自动模式选出 3 台最高优先级泵", "scan_ms": 10, "steps": [
            {"inputs": {"mode": True, "start": True, "stop": False,
                        "pumpGroup": [
                            {"priority": 5, "selection": False},
                            {"priority": 1, "selection": False},
                            {"priority": 4, "selection": False},
                            {"priority": 2, "selection": False},
                            {"priority": 3, "selection": False}]},
             "expect": {"pumpGroup": [{"RunComd": True}, {"RunComd": False},
                                      {"RunComd": True}, {"RunComd": False},
                                      {"RunComd": True}]}},
        ]},
        {"id": "TC3", "description": "停止优先于启动", "scan_ms": 10, "steps": [
            {"inputs": {"mode": True, "start": True, "stop": False,
                        "pumpGroup": [
                            {"priority": 5, "selection": False},
                            {"priority": 1, "selection": False},
                            {"priority": 4, "selection": False},
                            {"priority": 2, "selection": False},
                            {"priority": 3, "selection": False}]},
             "expect": {"pumpGroup": [{"RunComd": True}, {"RunComd": False},
                                      {"RunComd": True}, {"RunComd": False},
                                      {"RunComd": True}]}},
            {"inputs": {"mode": True, "start": True, "stop": True,
                        "pumpGroup": [
                            {"priority": 5, "selection": False},
                            {"priority": 1, "selection": False},
                            {"priority": 4, "selection": False},
                            {"priority": 2, "selection": False},
                            {"priority": 3, "selection": False}]},
             "expect": {"pumpGroup": [{"RunComd": False}, {"RunComd": False},
                                      {"RunComd": False}, {"RunComd": False},
                                      {"RunComd": False}]}},
        ]},
    ],
    "reference": {
        "auto_wire": False,
        "duts": [
            {"name": "ST_Pump", "kind": "struct",
             "declaration": "TYPE ST_Pump :\nSTRUCT\n    priority : INT;\n    selection : BOOL;\n    RunComd : BOOL;\nEND_STRUCT\nEND_TYPE\n"},
        ],
        "pous": [
            {
                "name": "MultiPump",
                "kind": "function_block",
                "declaration": (
                    "FUNCTION_BLOCK MultiPump\n"
                    "VAR_INPUT\n"
                    "    mode : BOOL;\n"
                    "    start : BOOL;\n"
                    "    stop : BOOL;\n"
                    "END_VAR\n"
                    "VAR_IN_OUT\n"
                    "    pumpGroup : ARRAY[1..5] OF ST_Pump;\n"
                    "END_VAR\n"
                    "VAR\n"
                    "    i : INT;\n"
                    "    j : INT;\n"
                    "    higher : INT;\n"
                    "END_VAR\n"),
                "implementation": (
                    "FOR i := 1 TO 5 DO\n"
                    "    IF stop THEN\n"
                    "        pumpGroup[i].RunComd := FALSE;\n"
                    "    ELSIF start THEN\n"
                    "        IF mode THEN\n"
                    "            higher := 0;\n"
                    "            FOR j := 1 TO 5 DO\n"
                    "                IF pumpGroup[j].priority > pumpGroup[i].priority THEN\n"
                    "                    higher := higher + 1;\n"
                    "                END_IF\n"
                    "            END_FOR\n"
                    "            IF higher < 3 THEN\n"
                    "                pumpGroup[i].RunComd := TRUE;\n"
                    "            ELSE\n"
                    "                pumpGroup[i].RunComd := FALSE;\n"
                    "            END_IF\n"
                    "        ELSE\n"
                    "            pumpGroup[i].RunComd := pumpGroup[i].selection;\n"
                    "        END_IF\n"
                    "    END_IF\n"
                    "END_FOR\n"),
            },
            {
                "name": "PLC_PRG",
                "kind": "program",
                "declaration": (
                    "PROGRAM PLC_PRG\n"
                    "VAR\n"
                    "    fb : MultiPump;\n"
                    "    pumps : ARRAY[1..5] OF ST_Pump;\n"
                    "END_VAR\n"),
                "implementation": (
                    "fb(mode := FALSE, start := FALSE, stop := FALSE, pumpGroup := pumps);\n"),
            },
        ],
    },
})

# ---------------------------------------------------------------------------
# medium 2: Calculate Moving Average
# ---------------------------------------------------------------------------
TASKS.append({
    "id": "public_medium_002",
    "source": "public",
    "difficulty": "medium",
    "title": "移动平均计算",
    "pou": {"type": "function_block", "name": "MovingAverage"},
    "requirement": {
        "en": (
            "Calculate a moving arithmetic mean over a window. cyclicExecution TRUE "
            "reads a new value each cycle; a rising edge of trigger also reads a new "
            "value; reset clears the average; windowSize outside 1..100 sets error and "
            "status 16#8200."
        ),
        "zh": (
            "计算滑动算术平均。cyclicExecution 为 TRUE 时每个周期读入新值并更新平均；"
            "trigger 的上升沿也读入新值并更新；reset 为 TRUE 时复位计算；windowSize 不在 "
            "1..100 时输出错误并置状态码 16#8200。"
        ),
    },
    "interface": {
        "duts": [],
        "inputs": [
            {"name": "cyclicExecution", "type": "BOOL", "desc": "周期读取"},
            {"name": "trigger", "type": "BOOL", "desc": "外部触发"},
            {"name": "value", "type": "LREAL", "desc": "新数据值"},
            {"name": "windowSize", "type": "INT", "desc": "窗口大小 1..100"},
            {"name": "reset", "type": "BOOL", "desc": "复位信号"},
        ],
        "outputs": [
            {"name": "average", "type": "LREAL", "desc": "滑动平均"},
            {"name": "windowSizeReached", "type": "BOOL", "desc": "是否达到最大窗口"},
            {"name": "error", "type": "BOOL", "desc": "错误"},
            {"name": "status", "type": "WORD", "desc": "状态码"},
        ],
        "inouts": [],
    },
    "ltl_specs": [
        {"id": "P1", "description": "窗口长度非法时报错。",
         "formula": "G((windowSize < 1 || windowSize > 100) -> error)"},
        {"id": "P2", "description": "无错误时状态码为 0。",
         "formula": "G(!error -> status = 0)"},
    ],
    "test_cases": [
        {"id": "TC1", "description": "窗口滑动平均", "scan_ms": 10, "steps": [
            {"inputs": {"cyclicExecution": True, "trigger": False, "value": 1.0,
                        "windowSize": 3, "reset": False},
             "expect": {"average": 1.0, "windowSizeReached": False, "error": False}},
            {"inputs": {"cyclicExecution": True, "trigger": False, "value": 2.0,
                        "windowSize": 3, "reset": False},
             "expect": {"average": 1.5, "windowSizeReached": False, "error": False}},
            {"inputs": {"cyclicExecution": True, "trigger": False, "value": 3.0,
                        "windowSize": 3, "reset": False},
             "expect": {"average": 2.0, "windowSizeReached": True, "error": False}},
            {"inputs": {"cyclicExecution": True, "trigger": False, "value": 4.0,
                        "windowSize": 3, "reset": False},
             "expect": {"average": 3.0, "windowSizeReached": True, "error": False}},
        ]},
        {"id": "TC2", "description": "窗口长度非法报错", "scan_ms": 10, "steps": [
            {"inputs": {"cyclicExecution": False, "trigger": False, "value": 1.0,
                        "windowSize": 0, "reset": False},
             "expect": {"error": True, "status": 33280}},
        ]},
    ],
    "reference": {
        "duts": [],
        "pous": [{
            "name": "MovingAverage",
            "kind": "function_block",
            "declaration": (
                "FUNCTION_BLOCK MovingAverage\n"
                "VAR_INPUT\n"
                "    cyclicExecution : BOOL;\n"
                "    trigger : BOOL;\n"
                "    value : LREAL;\n"
                "    windowSize : INT;\n"
                "    reset : BOOL;\n"
                "END_VAR\n"
                "VAR_OUTPUT\n"
                "    average : LREAL;\n"
                "    windowSizeReached : BOOL;\n"
                "    error : BOOL;\n"
                "    status : WORD;\n"
                "END_VAR\n"
                "VAR\n"
                "    buffer : ARRAY[1..100] OF LREAL;\n"
                "    head : INT := 0;\n"
                "    count : INT := 0;\n"
                "    sum : LREAL := 0.0;\n"
                "    trigPrev : BOOL;\n"
                "    trigRising : BOOL;\n"
                "END_VAR\n"),
            "implementation": (
                "error := FALSE;\n"
                "status := 0;\n"
                "IF reset THEN\n"
                "    head := 0;\n"
                "    count := 0;\n"
                "    sum := 0.0;\n"
                "    average := 0.0;\n"
                "    windowSizeReached := FALSE;\n"
                "END_IF\n"
                "IF windowSize < 1 OR windowSize > 100 THEN\n"
                "    error := TRUE;\n"
                "    status := 16#8200;\n"
                "ELSE\n"
                "    trigRising := trigger AND NOT trigPrev;\n"
                "    trigPrev := trigger;\n"
                "    IF cyclicExecution OR trigRising THEN\n"
                "        IF count < windowSize THEN\n"
                "            count := count + 1;\n"
                "            head := count;\n"
                "            buffer[head] := value;\n"
                "            sum := sum + value;\n"
                "        ELSE\n"
                "            head := head + 1;\n"
                "            IF head > windowSize THEN\n"
                "                head := 1;\n"
                "            END_IF\n"
                "            sum := sum - buffer[head] + value;\n"
                "            buffer[head] := value;\n"
                "        END_IF\n"
                "        windowSizeReached := (count >= windowSize);\n"
                "        IF windowSizeReached THEN\n"
                "            average := sum / INT_TO_LREAL(windowSize);\n"
                "        END_IF\n"
                "    END_IF\n"
                "END_IF\n"),
        }],
    },
})

# ---------------------------------------------------------------------------
# medium 3: Temperature Logic Control (TON state machine)
# ---------------------------------------------------------------------------
TASKS.append({
    "id": "public_medium_003",
    "source": "public",
    "difficulty": "medium",
    "title": "温度控制逻辑",
    "pou": {"type": "function_block", "name": "TempControl"},
    "requirement": {
        "en": (
            "Compare TemperatureSensorInput with SetTemperature: heat when below, stop "
            "when above. If the heater runs continuously over 5s, trigger overheat "
            "protection, turn off the heater and wait 3s before lifting. Temperature "
            "sensor below 0 or above 100 is a fault and turns the heater off."
        ),
        "zh": (
            "比较 TemperatureSensorInput 与 SetTemperature：低于设定值加热，高于设定值停止。"
            "若加热器连续工作超过 5s 则触发过热保护、自动关断，并须等待 3s 后才能解除保护。"
            "温度传感器读数小于 0 或大于 100 视为传感器故障，关断加热器。"
        ),
    },
    "interface": {
        "duts": [],
        "inputs": [
            {"name": "TemperatureSensorInput", "type": "REAL", "desc": "实际温度"},
            {"name": "SetTemperature", "type": "REAL", "desc": "设定温度"},
        ],
        "outputs": [
            {"name": "CurrentTemperature", "type": "REAL", "desc": "当前温度显示"},
            {"name": "SetTempDisplay", "type": "REAL", "desc": "设定温度显示"},
            {"name": "HeaterStatus", "type": "BOOL", "desc": "加热器状态显示"},
            {"name": "OverheatProtection", "type": "BOOL", "desc": "过热保护状态"},
            {"name": "HeaterOutput", "type": "BOOL", "desc": "加热器控制输出"},
        ],
        "inouts": [],
    },
    "ltl_specs": [
        {"id": "P1", "description": "传感器故障时关断加热器。",
         "formula": "G((TemperatureSensorInput < 0 || TemperatureSensorInput > 100) -> !HeaterOutput)"},
        {"id": "P2", "description": "低温且无故障/保护时加热。",
         "formula": "G((TemperatureSensorInput < SetTemperature && !OverheatProtection) -> HeaterOutput)"},
        {"id": "P3", "description": "过热保护时禁止加热。",
         "formula": "G(OverheatProtection -> !HeaterOutput)"},
    ],
    "test_cases": [
        {"id": "TC1", "description": "低温加热高温停止", "scan_ms": 1000, "steps": [
            {"inputs": {"TemperatureSensorInput": 30.0, "SetTemperature": 50.0},
             "expect": {"HeaterOutput": True, "OverheatProtection": False}},
            {"inputs": {"TemperatureSensorInput": 60.0, "SetTemperature": 50.0},
             "expect": {"HeaterOutput": False, "OverheatProtection": False}},
        ]},
        {"id": "TC2", "description": "传感器故障关断", "scan_ms": 1000, "steps": [
            {"inputs": {"TemperatureSensorInput": 150.0, "SetTemperature": 50.0},
             "expect": {"HeaterOutput": False}},
        ]},
        {"id": "TC3", "description": "过热保护与恢复", "scan_ms": 1000, "steps": [
            {"inputs": {"TemperatureSensorInput": 30.0, "SetTemperature": 50.0},
             "expect": {"HeaterOutput": True, "OverheatProtection": False}},
            {"inputs": {"TemperatureSensorInput": 30.0, "SetTemperature": 50.0},
             "expect": {"HeaterOutput": True, "OverheatProtection": False}},
            {"inputs": {"TemperatureSensorInput": 30.0, "SetTemperature": 50.0},
             "expect": {"HeaterOutput": True, "OverheatProtection": False}},
            {"inputs": {"TemperatureSensorInput": 30.0, "SetTemperature": 50.0},
             "expect": {"HeaterOutput": True, "OverheatProtection": False}},
            {"inputs": {"TemperatureSensorInput": 30.0, "SetTemperature": 50.0},
             "expect": {"HeaterOutput": False, "OverheatProtection": True}},
            {"inputs": {"TemperatureSensorInput": 30.0, "SetTemperature": 50.0},
             "expect": {"HeaterOutput": False, "OverheatProtection": True}},
            {"inputs": {"TemperatureSensorInput": 30.0, "SetTemperature": 50.0},
             "expect": {"HeaterOutput": False, "OverheatProtection": True}},
            {"inputs": {"TemperatureSensorInput": 30.0, "SetTemperature": 50.0},
             "expect": {"HeaterOutput": False, "OverheatProtection": False}},
            {"inputs": {"TemperatureSensorInput": 30.0, "SetTemperature": 50.0},
             "expect": {"HeaterOutput": True, "OverheatProtection": False}},
        ]},
    ],
    "reference": {
        "duts": [],
        "pous": [{
            "name": "TempControl",
            "kind": "function_block",
            "declaration": (
                "FUNCTION_BLOCK TempControl\n"
                "VAR_INPUT\n"
                "    TemperatureSensorInput : REAL;\n"
                "    SetTemperature : REAL;\n"
                "END_VAR\n"
                "VAR_OUTPUT\n"
                "    CurrentTemperature : REAL;\n"
                "    SetTempDisplay : REAL;\n"
                "    HeaterStatus : BOOL;\n"
                "    OverheatProtection : BOOL;\n"
                "    HeaterOutput : BOOL;\n"
                "END_VAR\n"
                "VAR\n"
                "    phase : INT := 0;\n"
                "    heatCmd : BOOL;\n"
                "    heatTimer : TON;\n"
                "    coolTimer : TON;\n"
                "END_VAR\n"),
            "implementation": (
                "CurrentTemperature := TemperatureSensorInput;\n"
                "SetTempDisplay := SetTemperature;\n"
                "CASE phase OF\n"
                "0:\n"
                "    IF TemperatureSensorInput < 0.0 OR TemperatureSensorInput > 100.0 THEN\n"
                "        heatCmd := FALSE;\n"
                "    ELSIF TemperatureSensorInput < SetTemperature THEN\n"
                "        heatCmd := TRUE;\n"
                "    ELSIF TemperatureSensorInput > SetTemperature THEN\n"
                "        heatCmd := FALSE;\n"
                "    END_IF\n"
                "    heatTimer(IN := heatCmd, PT := T#5s);\n"
                "    IF heatTimer.Q THEN\n"
                "        phase := 1;\n"
                "        HeaterOutput := FALSE;\n"
                "    ELSE\n"
                "        HeaterOutput := heatCmd;\n"
                "    END_IF\n"
                "1:\n"
                "    HeaterOutput := FALSE;\n"
                "    coolTimer(IN := TRUE, PT := T#3s);\n"
                "    IF coolTimer.Q THEN\n"
                "        phase := 0;\n"
                "        heatTimer(IN := FALSE, PT := T#5s);\n"
                "        coolTimer(IN := FALSE, PT := T#3s);\n"
                "    END_IF\n"
                "END_CASE\n"
                "OverheatProtection := (phase = 1);\n"
                "HeaterStatus := HeaterOutput;\n"),
        }],
    },
})


# ---------------------------------------------------------------------------
# medium 4: Analog Batch Processing (struct + ARRAY[*] + caller)
# ---------------------------------------------------------------------------
TASKS.append({
    "id": "public_medium_004",
    "source": "public",
    "difficulty": "medium",
    "title": "模拟量批处理转换",
    "pou": {"type": "function_block", "name": "AnalogBatch"},
    "requirement": {
        "en": (
            "Process analogValues in batches into engineering values. count is how "
            "many channels to process; match channels by ordinal position from each "
            "array's lower bound. Per channel, if enabled convert by measuringMode "
            "(0 linear 0/+-27648 to loLIM..hiLIM; 1 standard temperature =raw/10; "
            "2 climatic temperature =raw/100). Invalid mode sets retVal 16#8001; "
            "hiLIM<=loLIM sets retVal 16#8002."
        ),
        "zh": (
            "批量把模拟量原始值 analogValues 转换为工程量。count 为要处理的通道数，按各自数组"
            "下界对齐通道。每通道若 enable 则按 measuringMode 转换：0 线性(单极性 0..27648、"
            "双极性 -27648..27648 映射到 loLIM..hiLIM)、1 标准温度(原值/10)、2 气候温度(原值/100)。"
            "模式非法置 retVal 16#8001；hiLIM<=loLIM 置 retVal 16#8002。"
        ),
    },
    "interface": {
        "duts": [
            {"name": "ST_AnalogChannel", "kind": "struct", "fields": [
                {"name": "enable", "type": "BOOL", "desc": "转换使能"},
                {"name": "hiLIM", "type": "REAL", "desc": "工程量上限"},
                {"name": "loLIM", "type": "REAL", "desc": "工程量下限"},
                {"name": "bipolar", "type": "BOOL", "desc": "FALSE 单极性 TRUE 双极性"},
                {"name": "measuringMode", "type": "INT", "desc": "0 线性 1 标准温度 2 气候温度"},
                {"name": "retVal", "type": "WORD", "desc": "状态码"},
                {"name": "outputValue", "type": "REAL", "desc": "转换结果"},
            ]},
        ],
        "inputs": [
            {"name": "count", "type": "DINT", "desc": "待转换通道数"},
        ],
        "outputs": [],
        "inouts": [
            {"name": "analogValues", "type": "ARRAY[*] OF INT", "desc": "原始值数组(只读)"},
            {"name": "channels", "type": "ARRAY[*] OF ST_AnalogChannel", "desc": "通道记录(写 retVal/outputValue)"},
        ],
    },
    "ltl_specs": [
        {"id": "P1", "description": "模式非法时报 16#8001。",
         "formula": "G((channels[0].enable && (channels[0].measuringMode < 0 || channels[0].measuringMode > 2)) -> channels[0].retVal = 16#8001)"},
        {"id": "P2", "description": "上下限非法时报 16#8002。",
         "formula": "G((channels[0].enable && channels[0].hiLIM <= channels[0].loLIM) -> channels[0].retVal = 16#8002)"},
    ],
    "test_cases": [
        {"id": "TC1", "description": "线性转换", "scan_ms": 10, "steps": [
            {"inputs": {"count": 1,
                        "analogValues": [0],
                        "channels": [{"enable": True, "hiLIM": 100.0, "loLIM": 0.0,
                                      "bipolar": False, "measuringMode": 0}]},
             "expect": {"channels": [{"retVal": 0, "outputValue": 0.0}]}},
            {"inputs": {"count": 1,
                        "analogValues": [13824],
                        "channels": [{"enable": True, "hiLIM": 100.0, "loLIM": 0.0,
                                      "bipolar": False, "measuringMode": 0}]},
             "expect": {"channels": [{"retVal": 0, "outputValue": 50.0}]}},
        ]},
        {"id": "TC2", "description": "模式非法与上下限非法", "scan_ms": 10, "steps": [
            {"inputs": {"count": 1, "analogValues": [0],
                        "channels": [{"enable": True, "hiLIM": 100.0, "loLIM": 0.0,
                                      "bipolar": False, "measuringMode": 5}]},
             "expect": {"channels": [{"retVal": 32769}]}},
            {"inputs": {"count": 1, "analogValues": [0],
                        "channels": [{"enable": True, "hiLIM": 10.0, "loLIM": 20.0,
                                      "bipolar": False, "measuringMode": 0}]},
             "expect": {"channels": [{"retVal": 32770}]}},
        ]},
    ],
    "reference": {
        "auto_wire": False,
        "duts": [
            {"name": "ST_AnalogChannel", "kind": "struct",
             "declaration": "TYPE ST_AnalogChannel :\nSTRUCT\n    enable : BOOL;\n    hiLIM : REAL;\n    loLIM : REAL;\n    bipolar : BOOL;\n    measuringMode : INT;\n    retVal : WORD;\n    outputValue : REAL;\nEND_STRUCT\nEND_TYPE\n"},
        ],
        "pous": [
            {
                "name": "AnalogBatch",
                "kind": "function_block",
                "declaration": (
                    "FUNCTION_BLOCK AnalogBatch\n"
                    "VAR_INPUT\n"
                    "    count : DINT;\n"
                    "END_VAR\n"
                    "VAR_IN_OUT\n"
                    "    analogValues : ARRAY[*] OF INT;\n"
                    "    channels : ARRAY[*] OF ST_AnalogChannel;\n"
                    "END_VAR\n"
                    "VAR\n"
                    "    i : DINT;\n"
                    "    cidx : DINT;\n"
                    "    aidx : DINT;\n"
                    "    raw : INT;\n"
                    "    rawMin : INT;\n"
                    "    rawMax : INT;\n"
                    "    mode : INT;\n"
                    "END_VAR\n"),
                "implementation": (
                    "FOR i := 0 TO count - 1 DO\n"
                    "    cidx := LOWER_BOUND(channels, 1) + i;\n"
                    "    aidx := LOWER_BOUND(analogValues, 1) + i;\n"
                    "    IF channels[cidx].enable THEN\n"
                    "        mode := channels[cidx].measuringMode;\n"
                    "        IF mode < 0 OR mode > 2 THEN\n"
                    "            channels[cidx].retVal := 16#8001;\n"
                    "        ELSIF channels[cidx].hiLIM <= channels[cidx].loLIM THEN\n"
                    "            channels[cidx].retVal := 16#8002;\n"
                    "        ELSE\n"
                    "            raw := analogValues[aidx];\n"
                    "            IF mode = 0 THEN\n"
                    "                IF channels[cidx].bipolar THEN\n"
                    "                    rawMin := -27648;\n"
                    "                    rawMax := 27648;\n"
                    "                ELSE\n"
                    "                    rawMin := 0;\n"
                    "                    rawMax := 27648;\n"
                    "                END_IF\n"
                    "                channels[cidx].outputValue := channels[cidx].loLIM\n"
                    "                    + (INT_TO_REAL(raw - rawMin) / INT_TO_REAL(rawMax - rawMin))\n"
                    "                    * (channels[cidx].hiLIM - channels[cidx].loLIM);\n"
                    "            ELSIF mode = 1 THEN\n"
                    "                channels[cidx].outputValue := INT_TO_REAL(raw) / 10.0;\n"
                    "            ELSE\n"
                    "                channels[cidx].outputValue := INT_TO_REAL(raw) / 100.0;\n"
                    "            END_IF\n"
                    "            channels[cidx].retVal := 0;\n"
                    "        END_IF\n"
                    "    END_IF\n"
                    "END_FOR\n"),
            },
            {
                "name": "PLC_PRG",
                "kind": "program",
                "declaration": (
                    "PROGRAM PLC_PRG\n"
                    "VAR\n"
                    "    fb : AnalogBatch;\n"
                    "    avals : ARRAY[0..9] OF INT;\n"
                    "    chans : ARRAY[0..9] OF ST_AnalogChannel;\n"
                    "END_VAR\n"),
                "implementation": "fb(count := 1, analogValues := avals, channels := chans);\n",
            },
        ],
    },
})

# ---------------------------------------------------------------------------
# medium 5: Automated Production Line Control
# ---------------------------------------------------------------------------
TASKS.append({
    "id": "public_medium_005",
    "source": "public",
    "difficulty": "medium",
    "title": "自动化生产线控制",
    "pou": {"type": "function_block", "name": "ProductionLine"},
    "requirement": {
        "en": (
            "A line moves a product through stations A, B, C. Mode switches manual/"
            "automatic. Manual: ForwardButton drives forward, ReverseButton reverse, "
            "interlocked. Automatic: SensorA+ButtonA moves forward to B; SensorB stops, "
            "ButtonB moves to C; SensorC stops, ButtonC turns on CompletionLight; when "
            "SensorC clears the light turns off."
        ),
        "zh": (
            "生产线把产品依次送过工位 A、B、C。Mode 切换手动/自动。手动：ForwardButton 正转、"
            "ReverseButton 反转，且互锁不可同时。自动：SensorA 检测到产品且 ButtonA 确认后正转"
            "送向 B；SensorB 检测到后停止，ButtonB 确认后正转送向 C；SensorC 检测到后停止，"
            "ButtonC 确认后点亮 CompletionLight；产品被取走(SensorC 消失)后熄灭。"
        ),
    },
    "interface": {
        "duts": [],
        "inputs": [
            {"name": "Mode", "type": "BOOL", "desc": "0 手动 1 自动"},
            {"name": "ForwardButton", "type": "BOOL", "desc": "正转按钮"},
            {"name": "ReverseButton", "type": "BOOL", "desc": "反转按钮"},
            {"name": "SensorA", "type": "BOOL", "desc": "A 工位传感器"},
            {"name": "SensorB", "type": "BOOL", "desc": "B 工位传感器"},
            {"name": "SensorC", "type": "BOOL", "desc": "C 工位传感器"},
            {"name": "ButtonA", "type": "BOOL", "desc": "A 工位完成按钮"},
            {"name": "ButtonB", "type": "BOOL", "desc": "B 工位完成按钮"},
            {"name": "ButtonC", "type": "BOOL", "desc": "C 工位完成按钮"},
        ],
        "outputs": [
            {"name": "MotorForward", "type": "BOOL", "desc": "正转输出"},
            {"name": "MotorReverse", "type": "BOOL", "desc": "反转输出"},
            {"name": "CompletionLight", "type": "BOOL", "desc": "完成指示灯"},
        ],
        "inouts": [],
    },
    "ltl_specs": [
        {"id": "P1", "description": "正反转互锁。",
         "formula": "G(!(MotorForward && MotorReverse))"},
        {"id": "P2", "description": "手动正转。",
         "formula": "G((!Mode && ForwardButton && !ReverseButton) -> MotorForward)"},
        {"id": "P3", "description": "完成灯只在产品位于 C 工位时点亮。",
         "formula": "G(CompletionLight -> SensorC)"},
    ],
    "test_cases": [
        {"id": "TC1", "description": "手动正反转与互锁", "scan_ms": 10, "steps": [
            {"inputs": {"Mode": False, "ForwardButton": True, "ReverseButton": False,
                        "SensorA": False, "SensorB": False, "SensorC": False,
                        "ButtonA": False, "ButtonB": False, "ButtonC": False},
             "expect": {"MotorForward": True, "MotorReverse": False}},
            {"inputs": {"Mode": False, "ForwardButton": False, "ReverseButton": True,
                        "SensorA": False, "SensorB": False, "SensorC": False,
                        "ButtonA": False, "ButtonB": False, "ButtonC": False},
             "expect": {"MotorForward": False, "MotorReverse": True}},
            {"inputs": {"Mode": False, "ForwardButton": True, "ReverseButton": True,
                        "SensorA": False, "SensorB": False, "SensorC": False,
                        "ButtonA": False, "ButtonB": False, "ButtonC": False},
             "expect": {"MotorForward": False, "MotorReverse": False}},
        ]},
        {"id": "TC2", "description": "自动流程 A→B→C", "scan_ms": 10, "steps": [
            {"inputs": {"Mode": True, "ForwardButton": False, "ReverseButton": False,
                        "SensorA": True, "SensorB": False, "SensorC": False,
                        "ButtonA": True, "ButtonB": False, "ButtonC": False},
             "expect": {}},
            {"inputs": {"Mode": True, "ForwardButton": False, "ReverseButton": False,
                        "SensorA": False, "SensorB": False, "SensorC": False,
                        "ButtonA": False, "ButtonB": False, "ButtonC": False},
             "expect": {"MotorForward": True}},
            {"inputs": {"Mode": True, "ForwardButton": False, "ReverseButton": False,
                        "SensorA": False, "SensorB": True, "SensorC": False,
                        "ButtonA": False, "ButtonB": False, "ButtonC": False},
             "expect": {"MotorForward": False}},
            {"inputs": {"Mode": True, "ForwardButton": False, "ReverseButton": False,
                        "SensorA": False, "SensorB": True, "SensorC": False,
                        "ButtonA": False, "ButtonB": True, "ButtonC": False},
             "expect": {}},
            {"inputs": {"Mode": True, "ForwardButton": False, "ReverseButton": False,
                        "SensorA": False, "SensorB": False, "SensorC": False,
                        "ButtonA": False, "ButtonB": False, "ButtonC": False},
             "expect": {"MotorForward": True}},
            {"inputs": {"Mode": True, "ForwardButton": False, "ReverseButton": False,
                        "SensorA": False, "SensorB": False, "SensorC": True,
                        "ButtonA": False, "ButtonB": False, "ButtonC": False},
             "expect": {"MotorForward": False}},
            {"inputs": {"Mode": True, "ForwardButton": False, "ReverseButton": False,
                        "SensorA": False, "SensorB": False, "SensorC": True,
                        "ButtonA": False, "ButtonB": False, "ButtonC": True},
             "expect": {}},
            {"inputs": {"Mode": True, "ForwardButton": False, "ReverseButton": False,
                        "SensorA": False, "SensorB": False, "SensorC": True,
                        "ButtonA": False, "ButtonB": False, "ButtonC": False},
             "expect": {"CompletionLight": True}},
        ]},
    ],
    "reference": {
        "duts": [],
        "pous": [{
            "name": "ProductionLine",
            "kind": "function_block",
            "declaration": (
                "FUNCTION_BLOCK ProductionLine\n"
                "VAR_INPUT\n"
                "    Mode : BOOL;\n"
                "    ForwardButton : BOOL;\n"
                "    ReverseButton : BOOL;\n"
                "    SensorA : BOOL;\n"
                "    SensorB : BOOL;\n"
                "    SensorC : BOOL;\n"
                "    ButtonA : BOOL;\n"
                "    ButtonB : BOOL;\n"
                "    ButtonC : BOOL;\n"
                "END_VAR\n"
                "VAR_OUTPUT\n"
                "    MotorForward : BOOL;\n"
                "    MotorReverse : BOOL;\n"
                "    CompletionLight : BOOL;\n"
                "END_VAR\n"
                "VAR\n"
                "    stage : INT := 0;\n"
                "END_VAR\n"),
            "implementation": (
                "MotorForward := FALSE;\n"
                "MotorReverse := FALSE;\n"
                "CompletionLight := FALSE;\n"
                "IF NOT Mode THEN\n"
                "    IF ReverseButton AND NOT ForwardButton THEN\n"
                "        MotorReverse := TRUE;\n"
                "    ELSIF ForwardButton AND NOT ReverseButton THEN\n"
                "        MotorForward := TRUE;\n"
                "    END_IF\n"
                "    stage := 0;\n"
                "ELSE\n"
                "    CASE stage OF\n"
                "    0:\n"
                "        IF SensorA AND ButtonA THEN\n"
                "            stage := 1;\n"
                "        END_IF\n"
                "    1:\n"
                "        MotorForward := TRUE;\n"
                "        IF SensorB THEN\n"
                "            stage := 2;\n"
                "        END_IF\n"
                "    2:\n"
                "        IF ButtonB THEN\n"
                "            stage := 3;\n"
                "        END_IF\n"
                "    3:\n"
                "        MotorForward := TRUE;\n"
                "        IF SensorC THEN\n"
                "            stage := 4;\n"
                "        END_IF\n"
                "    4:\n"
                "        IF ButtonC THEN\n"
                "            stage := 5;\n"
                "        END_IF\n"
                "    5:\n"
                "        CompletionLight := TRUE;\n"
                "        IF NOT SensorC THEN\n"
                "            stage := 0;\n"
                "        END_IF\n"
                "    END_CASE\n"
                "END_IF\n"),
        }],
    },
})

# ---------------------------------------------------------------------------
# medium 6: Slab Thickness Alarm and Fault History
# ---------------------------------------------------------------------------
TASKS.append({
    "id": "public_medium_006",
    "source": "public",
    "difficulty": "medium",
    "title": "板厚报警与故障历史",
    "pou": {"type": "function_block", "name": "SlabThickness"},
    "requirement": {
        "en": (
            "Monitor slab-thickness faults: when signal valid, alarm immediately on "
            "fault and hold each alarm at least 500ms; on each valid fault rising edge "
            "increment counter and store FaultTimestamp into history[0] shifting older "
            "entries; accumulate runtime by CycleTime only while cutting and no fault; "
            "on power-up or invalid signal clear alarm and hold state."
        ),
        "zh": (
            "监控板厚故障：信号有效时，故障为 TRUE 立即报警且每次报警至少保持 500ms；每次有效"
            "故障上升沿使计数器加 1 并把 FaultTimestamp 存入 history[0]、旧记录右移；仅在切割运行"
            "且无故障时按 CycleTime 累加运行时间；上电或信号无效时关断报警并清除保持状态。"
        ),
    },
    "interface": {
        "duts": [],
        "inputs": [
            {"name": "THICKNESS_FAULT", "type": "BOOL", "desc": "厚度超差"},
            {"name": "THICKNESS_SIGNAL_VALID", "type": "BOOL", "desc": "信号有效"},
            {"name": "CUTTING_RUN", "type": "BOOL", "desc": "切割运行状态"},
            {"name": "FaultTimestamp", "type": "DINT", "desc": "故障时间戳(秒)"},
            {"name": "CycleTime", "type": "TIME", "desc": "调用间隔"},
        ],
        "outputs": [
            {"name": "THICKNESS_ALARM", "type": "BOOL", "desc": "报警(至少 500ms 保持)"},
            {"name": "Slab_Fault_Counter", "type": "UINT", "desc": "有效故障次数"},
            {"name": "Slab_Runtime_Accumulator", "type": "LTIME", "desc": "正常切割累计时间"},
            {"name": "Slab_Fault_History", "type": "ARRAY[0..4] OF DINT", "desc": "最近 5 条故障时间戳"},
        ],
        "inouts": [],
    },
    "ltl_specs": [
        {"id": "P1", "description": "信号无效时不报警。",
         "formula": "G(!THICKNESS_SIGNAL_VALID -> !THICKNESS_ALARM)"},
        {"id": "P2", "description": "报警意味着信号有效。",
         "formula": "G(THICKNESS_ALARM -> THICKNESS_SIGNAL_VALID)"},
        {"id": "P3", "description": "故障计数单调不减。",
         "formula": "G(Slab_Fault_Counter <= X(Slab_Fault_Counter))"},
    ],
    "test_cases": [
        {"id": "TC1", "description": "故障记录与计数", "scan_ms": 10, "steps": [
            {"inputs": {"THICKNESS_FAULT": False, "THICKNESS_SIGNAL_VALID": True,
                        "CUTTING_RUN": False, "FaultTimestamp": 0, "CycleTime": "T#10ms"},
             "expect": {"THICKNESS_ALARM": False, "Slab_Fault_Counter": 0}},
            {"inputs": {"THICKNESS_FAULT": True, "THICKNESS_SIGNAL_VALID": True,
                        "CUTTING_RUN": False, "FaultTimestamp": 100, "CycleTime": "T#10ms"},
             "expect": {"THICKNESS_ALARM": True, "Slab_Fault_Counter": 1,
                        "Slab_Fault_History": [100, 0, 0, 0, 0]}},
        ]},
        {"id": "TC2", "description": "信号无效时无记录", "scan_ms": 10, "steps": [
            {"inputs": {"THICKNESS_FAULT": True, "THICKNESS_SIGNAL_VALID": False,
                        "CUTTING_RUN": False, "FaultTimestamp": 100, "CycleTime": "T#10ms"},
             "expect": {"THICKNESS_ALARM": False, "Slab_Fault_Counter": 0}},
        ]},
    ],
    "reference": {
        "duts": [],
        "pous": [{
            "name": "SlabThickness",
            "kind": "function_block",
            "declaration": (
                "FUNCTION_BLOCK SlabThickness\n"
                "VAR_INPUT\n"
                "    THICKNESS_FAULT : BOOL;\n"
                "    THICKNESS_SIGNAL_VALID : BOOL;\n"
                "    CUTTING_RUN : BOOL;\n"
                "    FaultTimestamp : DINT;\n"
                "    CycleTime : TIME;\n"
                "END_VAR\n"
                "VAR_OUTPUT\n"
                "    THICKNESS_ALARM : BOOL;\n"
                "    Slab_Fault_Counter : UINT;\n"
                "    Slab_Runtime_Accumulator : LTIME;\n"
                "    Slab_Fault_History : ARRAY[0..4] OF DINT;\n"
                "END_VAR\n"
                "VAR\n"
                "    holdTof : TOF;\n"
                "    faultPrev : BOOL;\n"
                "    faultRising : BOOL;\n"
                "    i : INT;\n"
                "END_VAR\n"),
            "implementation": (
                "IF NOT THICKNESS_SIGNAL_VALID THEN\n"
                "    THICKNESS_ALARM := FALSE;\n"
                "    holdTof(IN := FALSE, PT := T#500ms);\n"
                "    faultPrev := THICKNESS_FAULT;\n"
                "ELSE\n"
                "    faultRising := THICKNESS_FAULT AND NOT faultPrev;\n"
                "    faultPrev := THICKNESS_FAULT;\n"
                "    IF faultRising THEN\n"
                "        Slab_Fault_Counter := Slab_Fault_Counter + 1;\n"
                "        FOR i := 4 TO 1 BY -1 DO\n"
                "            Slab_Fault_History[i] := Slab_Fault_History[i - 1];\n"
                "        END_FOR\n"
                "        Slab_Fault_History[0] := FaultTimestamp;\n"
                "    END_IF\n"
                "    holdTof(IN := THICKNESS_FAULT, PT := T#500ms);\n"
                "    THICKNESS_ALARM := THICKNESS_FAULT OR holdTof.Q;\n"
                "    IF CUTTING_RUN AND NOT THICKNESS_FAULT THEN\n"
                "        Slab_Runtime_Accumulator := Slab_Runtime_Accumulator + TO_LTIME(CycleTime);\n"
                "    END_IF\n"
                "END_IF\n"),
        }],
    },
})

# ---------------------------------------------------------------------------
# medium 7: Office HVAC Multi-mode Energy-Saving Control
# ---------------------------------------------------------------------------
TASKS.append({
    "id": "public_medium_007",
    "source": "public",
    "difficulty": "medium",
    "title": "办公楼 HVAC 多模式节能控制",
    "pou": {"type": "function_block", "name": "HVAC"},
    "requirement": {
        "en": (
            "Control a supply fan and temperature setpoint adjustment. Valid selector "
            "0 Auto, 1 Comfort, 2 Economy, 3 Night. Fan runs only after occupancy and "
            "non-Night mode hold for 30s. Auto: 0C occupied, +3C energy-saving or +2C "
            "standard unoccupied. Comfort: 0/+1. Economy: 0/+4. Night: +4 always. "
            "Clamp adjustment within +-4C."
        ),
        "zh": (
            "控制送风机与温度设定点偏移。selector 有效值 0 自动、1 舒适、2 经济、3 夜间。仅当有人"
            "且非夜间模式持续 30s 后风机才运行。自动：有人 0℃，无人节能 +3℃、标准 +2℃；舒适："
            "有人 0℃、无人 +1℃；经济：有人 0℃、无人 +4℃；夜间恒 +4℃。偏移限制在 ±4℃ 内。"
        ),
    },
    "interface": {
        "duts": [],
        "inputs": [
            {"name": "OCCUPANCY_DETECTED", "type": "BOOL", "desc": "有人检测"},
            {"name": "ENERGY_SAVING_MODE", "type": "BOOL", "desc": "节能选择"},
            {"name": "HVAC_MODE_SELECTOR", "type": "INT", "desc": "0 自动 1 舒适 2 经济 3 夜间"},
        ],
        "outputs": [
            {"name": "SUPPLY_FAN_RUN", "type": "BOOL", "desc": "送风机运行"},
            {"name": "TEMP_SETPOINT_ADJUST", "type": "INT", "desc": "温度设定点偏移(℃)"},
        ],
        "inouts": [],
    },
    "ltl_specs": [
        {"id": "P1", "description": "夜间模式风机不运行。",
         "formula": "G(HVAC_MODE_SELECTOR = 3 -> !SUPPLY_FAN_RUN)"},
        {"id": "P2", "description": "设定点偏移在 ±4℃ 内。",
         "formula": "G(TEMP_SETPOINT_ADJUST >= -4 && TEMP_SETPOINT_ADJUST <= 4)"},
        {"id": "P3", "description": "自动无人节能时偏移 +3℃。",
         "formula": "G((HVAC_MODE_SELECTOR = 0 && !OCCUPANCY_DETECTED && ENERGY_SAVING_MODE) -> TEMP_SETPOINT_ADJUST = 3)"},
    ],
    "test_cases": [
        {"id": "TC1", "description": "模式与偏移", "scan_ms": 1000, "steps": [
            {"inputs": {"OCCUPANCY_DETECTED": False, "ENERGY_SAVING_MODE": True, "HVAC_MODE_SELECTOR": 0},
             "expect": {"TEMP_SETPOINT_ADJUST": 3, "SUPPLY_FAN_RUN": False}},
            {"inputs": {"OCCUPANCY_DETECTED": True, "ENERGY_SAVING_MODE": True, "HVAC_MODE_SELECTOR": 0},
             "expect": {"TEMP_SETPOINT_ADJUST": 0, "SUPPLY_FAN_RUN": False}},
            {"inputs": {"OCCUPANCY_DETECTED": False, "ENERGY_SAVING_MODE": False, "HVAC_MODE_SELECTOR": 3},
             "expect": {"TEMP_SETPOINT_ADJUST": 4, "SUPPLY_FAN_RUN": False}},
        ]},
        {"id": "TC2", "description": "风机 30s 延时", "scan_ms": 1000, "steps": [
            {"inputs": {"OCCUPANCY_DETECTED": True, "ENERGY_SAVING_MODE": False, "HVAC_MODE_SELECTOR": 1},
             "expect": {"SUPPLY_FAN_RUN": False}},
            {"inputs": {"OCCUPANCY_DETECTED": True, "ENERGY_SAVING_MODE": False, "HVAC_MODE_SELECTOR": 1},
             "repeat": 29, "expect": {"SUPPLY_FAN_RUN": False}},
            {"inputs": {"OCCUPANCY_DETECTED": True, "ENERGY_SAVING_MODE": False, "HVAC_MODE_SELECTOR": 1},
             "repeat": 1, "expect": {"SUPPLY_FAN_RUN": True}},
        ]},
    ],
    "reference": {
        "duts": [],
        "pous": [{
            "name": "HVAC",
            "kind": "function_block",
            "declaration": (
                "FUNCTION_BLOCK HVAC\n"
                "VAR_INPUT\n"
                "    OCCUPANCY_DETECTED : BOOL;\n"
                "    ENERGY_SAVING_MODE : BOOL;\n"
                "    HVAC_MODE_SELECTOR : INT;\n"
                "END_VAR\n"
                "VAR_OUTPUT\n"
                "    SUPPLY_FAN_RUN : BOOL;\n"
                "    TEMP_SETPOINT_ADJUST : INT;\n"
                "END_VAR\n"
                "VAR\n"
                "    fanTon : TON;\n"
                "    adjust : INT;\n"
                "END_VAR\n"),
            "implementation": (
                "fanTon(IN := OCCUPANCY_DETECTED AND (HVAC_MODE_SELECTOR <> 3), PT := T#30s);\n"
                "SUPPLY_FAN_RUN := fanTon.Q;\n"
                "adjust := 0;\n"
                "CASE HVAC_MODE_SELECTOR OF\n"
                "0:\n"
                "    IF OCCUPANCY_DETECTED THEN\n"
                "        adjust := 0;\n"
                "    ELSIF ENERGY_SAVING_MODE THEN\n"
                "        adjust := 3;\n"
                "    ELSE\n"
                "        adjust := 2;\n"
                "    END_IF\n"
                "1:\n"
                "    IF OCCUPANCY_DETECTED THEN\n"
                "        adjust := 0;\n"
                "    ELSE\n"
                "        adjust := 1;\n"
                "    END_IF\n"
                "2:\n"
                "    IF OCCUPANCY_DETECTED THEN\n"
                "        adjust := 0;\n"
                "    ELSE\n"
                "        adjust := 4;\n"
                "    END_IF\n"
                "3:\n"
                "    adjust := 4;\n"
                "END_CASE\n"
                "IF adjust > 4 THEN\n"
                "    adjust := 4;\n"
                "END_IF\n"
                "IF adjust < -4 THEN\n"
                "    adjust := -4;\n"
                "END_IF\n"
                "TEMP_SETPOINT_ADJUST := adjust;\n"),
        }],
    },
})

# ---------------------------------------------------------------------------
# medium 8: IPv4 Parsing with Format and Range Checks
# ---------------------------------------------------------------------------
TASKS.append({
    "id": "public_medium_008",
    "source": "public",
    "difficulty": "medium",
    "title": "IPv4 地址解析",
    "pou": {"type": "function_block", "name": "IPv4Parse"},
    "requirement": {
        "en": (
            "Parse a dotted-decimal IPv4 string into a 32-bit unsigned integer. Four "
            "nonempty decimal segments separated by periods, each 0..255. Network byte "
            "order: first segment is the most significant byte. Zero on malformed input."
        ),
        "zh": (
            "把点分十进制 IPv4 字符串解析为 32 位无符号整数。要求四段非空十进制数、以句点分隔、"
            "每段 0..255，按网络字节序拼接(第一段为最高有效字节)。非法输入时 ipValue 置 0。"
        ),
    },
    "interface": {
        "duts": [],
        "inputs": [
            {"name": "ipText", "type": "STRING(254)", "desc": "待解析的 IPv4 文本"},
        ],
        "outputs": [
            {"name": "ipValue", "type": "UDINT", "desc": "32 位地址(网络字节序)，非法为 0"},
        ],
        "inouts": [],
    },
    "ltl_specs": [
        {"id": "P1", "description": "解析结果合法范围内。",
         "formula": "G(ipValue <= 16#FFFFFFFF)"},
    ],
    "test_cases": [
        {"id": "TC1", "description": "合法地址解析", "scan_ms": 10, "steps": [
            {"inputs": {"ipText": "192.168.1.1"},
             "expect": {"ipValue": 3232235777}},
            {"inputs": {"ipText": "0.0.0.0"},
             "expect": {"ipValue": 0}},
        ]},
        {"id": "TC2", "description": "非法地址置零", "scan_ms": 10, "steps": [
            {"inputs": {"ipText": "256.1.1.1"}, "expect": {"ipValue": 0}},
            {"inputs": {"ipText": "1.2.3"}, "expect": {"ipValue": 0}},
            {"inputs": {"ipText": "1.2.3.4.5"}, "expect": {"ipValue": 0}},
        ]},
    ],
    "reference": {
        "duts": [],
        "pous": [{
            "name": "IPv4Parse",
            "kind": "function_block",
            "declaration": (
                "FUNCTION_BLOCK IPv4Parse\n"
                "VAR_INPUT\n"
                "    ipText : STRING(254);\n"
                "END_VAR\n"
                "VAR_OUTPUT\n"
                "    ipValue : UDINT;\n"
                "END_VAR\n"
                "VAR\n"
                "    i : INT;\n"
                "    n : INT;\n"
                "    segCount : INT;\n"
                "    segVal : INT;\n"
                "    result : UDINT;\n"
                "    valid : BOOL;\n"
                "    started : BOOL;\n"
                "    ch : BYTE;\n"
                "END_VAR\n"),
            "implementation": (
                "n := LEN(ipText);\n"
                "segCount := 0;\n"
                "segVal := 0;\n"
                "result := 0;\n"
                "valid := TRUE;\n"
                "started := FALSE;\n"
                "FOR i := 1 TO n DO\n"
                "    ch := ipText[i];\n"
                "    IF ch = 46 THEN\n"
                "        IF NOT started OR segVal > 255 THEN\n"
                "            valid := FALSE;\n"
                "        END_IF\n"
                "        result := SHL(result, 8) OR INT_TO_UDINT(segVal);\n"
                "        segCount := segCount + 1;\n"
                "        segVal := 0;\n"
                "        started := FALSE;\n"
                "    ELSIF ch >= 48 AND ch <= 57 THEN\n"
                "        started := TRUE;\n"
                "        segVal := segVal * 10 + (BYTE_TO_INT(ch) - 48);\n"
                "        IF segVal > 255 THEN\n"
                "            valid := FALSE;\n"
                "        END_IF\n"
                "    ELSE\n"
                "        valid := FALSE;\n"
                "    END_IF\n"
                "END_FOR\n"
                "IF NOT started OR segVal > 255 THEN\n"
                "    valid := FALSE;\n"
                "END_IF\n"
                "result := SHL(result, 8) OR INT_TO_UDINT(segVal);\n"
                "segCount := segCount + 1;\n"
                "IF valid AND segCount = 4 THEN\n"
                "    ipValue := result;\n"
                "ELSE\n"
                "    ipValue := 0;\n"
                "END_IF\n"),
        }],
    },
})


def dump():
    os.makedirs(OUT, exist_ok=True)
    for t in TASKS:
        fn = os.path.join(OUT, t["id"] + ".json")
        with open(fn, "w", encoding="utf-8") as f:
            json.dump(t, f, ensure_ascii=False, indent=2)
        print("wrote", fn)


if __name__ == "__main__":
    dump()
