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
        {"id": "TC2", "description": "下降沿检测(新实例首拍为上升沿)", "scan_ms": 10, "steps": [
            {"inputs": {"value": 5},
             "expect": {"hasChanged": True, "hasRisingEdges": True,
                        "risingBits": 5, "noOfRisingBits": 2,
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
            {"inputs": {"Gap_Exceeded": True, "Weld_E_Stop_NC": True, "DebounceTime": "T#1s"},
             "repeat": 200, "expect": {"Weld_Soft_Start_Active": True, "Operator_Alert": False}},
            {"inputs": {"Gap_Exceeded": True, "Weld_E_Stop_NC": True, "DebounceTime": "T#1s"},
             "repeat": 60, "expect": {"Weld_Soft_Start_Active": False, "Operator_Alert": False}},
            {"inputs": {"Gap_Exceeded": True, "Weld_E_Stop_NC": True, "DebounceTime": "T#1s"},
             "repeat": 50, "expect": {"Operator_Alert": True}},
            {"inputs": {"Gap_Exceeded": False, "Weld_E_Stop_NC": True, "DebounceTime": "T#1s"},
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
             "expect": {"BLOWER_RUN": False, "AERATION_BLOWER_CYCLE_COUNT": 0}},
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
                "        average := sum / INT_TO_LREAL(count);\n"
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
             "repeat": 5, "expect": {"HeaterOutput": True, "OverheatProtection": False}},
            {"inputs": {"TemperatureSensorInput": 30.0, "SetTemperature": 50.0},
             "repeat": 1, "expect": {"HeaterOutput": False, "OverheatProtection": True}},
            {"inputs": {"TemperatureSensorInput": 30.0, "SetTemperature": 50.0},
             "repeat": 3, "expect": {"HeaterOutput": False, "OverheatProtection": True}},
            {"inputs": {"TemperatureSensorInput": 30.0, "SetTemperature": 50.0},
             "repeat": 1, "expect": {"HeaterOutput": False, "OverheatProtection": False}},
            {"inputs": {"TemperatureSensorInput": 30.0, "SetTemperature": 50.0},
             "repeat": 1, "expect": {"HeaterOutput": True, "OverheatProtection": False}},
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
             "expect": {"MotorForward": True}},
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
             "expect": {"MotorForward": True}},
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
                "FOR i := 0 TO n - 1 DO\n"
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


# ---------------------------------------------------------------------------
# hard 1: Recipe Management System (struct array + CRUD)
# ---------------------------------------------------------------------------
TASKS.append({
    "id": "public_hard_001",
    "source": "public",
    "difficulty": "hard",
    "title": "配方管理系统",
    "pou": {"type": "function_block", "name": "RecipeMgmt"},
    "requirement": {
        "en": (
            "Manage up to 10 recipes (ARRAY[1..10] OF ST_Recipe, recipeID 0 = empty "
            "slot). queryRecipe finds by recipeID (not found -> error 16#8001, else "
            "output recipeQueryResult). addRecipe: duplicate -> 16#8002, no empty slot "
            "-> 16#8003, else store in smallest empty slot. deleteRecipe: not found -> "
            "16#8004, else set recipeID 0. modifyRecipe: not found -> 16#8005, else "
            "replace."
        ),
        "zh": (
            "管理最多 10 条配方(ARRAY[1..10] OF ST_Recipe，recipeID=0 表示空槽)。queryRecipe 按 "
            "recipeID 查询(未找到 error 16#8001，否则输出 recipeQueryResult)。addRecipe：重复 16#8002、"
            "无空槽 16#8003，否则存入最小空槽。deleteRecipe：未找到 16#8004，否则置 recipeID=0。"
            "modifyRecipe：未找到 16#8005，否则替换。"
        ),
    },
    "interface": {
        "duts": [
            {"name": "ST_Recipe", "kind": "struct", "fields": [
                {"name": "recipeID", "type": "INT", "desc": "配方号，0 表示空槽"},
                {"name": "ingredientType", "type": "INT", "desc": "原料类型"},
                {"name": "ingredientRatio", "type": "REAL", "desc": "原料比例"},
                {"name": "productionTemperature", "type": "REAL", "desc": "生产温度"},
            ]},
        ],
        "inputs": [
            {"name": "addRecipe", "type": "BOOL", "desc": "添加请求"},
            {"name": "deleteRecipe", "type": "BOOL", "desc": "删除请求"},
            {"name": "modifyRecipe", "type": "BOOL", "desc": "修改请求"},
            {"name": "queryRecipe", "type": "BOOL", "desc": "查询请求"},
            {"name": "recipeIn", "type": "ST_Recipe", "desc": "输入配方"},
        ],
        "outputs": [
            {"name": "recipeAdded", "type": "BOOL", "desc": "添加成功"},
            {"name": "recipeDeleted", "type": "BOOL", "desc": "删除成功"},
            {"name": "recipeModified", "type": "BOOL", "desc": "修改成功"},
            {"name": "recipeQueryResult", "type": "ST_Recipe", "desc": "查询结果"},
            {"name": "error", "type": "BOOL", "desc": "错误"},
            {"name": "status", "type": "WORD", "desc": "状态码"},
        ],
        "inouts": [
            {"name": "recipe", "type": "ARRAY[1..10] OF ST_Recipe", "desc": "配方库"},
        ],
    },
    "ltl_specs": [
        {"id": "P1", "description": "无错误时状态码为 0。",
         "formula": "G(!error -> status = 0)"},
        {"id": "P2", "description": "错误时状态码属于合法错误码集合。",
         "formula": "G(error -> (status = 16#8001 || status = 16#8002 || status = 16#8003 || status = 16#8004 || status = 16#8005))"},
    ],
    "test_cases": [
        {"id": "TC1", "description": "添加与查询", "scan_ms": 10, "steps": [
            {"inputs": {"addRecipe": False, "deleteRecipe": False, "modifyRecipe": False,
                        "queryRecipe": False,
                        "recipeIn": {"recipeID": 0, "ingredientType": 0,
                                     "ingredientRatio": 0.0, "productionTemperature": 0.0}},
             "expect": {"error": False}},
            {"inputs": {"addRecipe": True, "deleteRecipe": False, "modifyRecipe": False,
                        "queryRecipe": False,
                        "recipeIn": {"recipeID": 1, "ingredientType": 5,
                                     "ingredientRatio": 30.0, "productionTemperature": 120.0}},
             "expect": {"recipeAdded": True, "error": False,
                        "recipe": [{"recipeID": 1, "ingredientType": 5,
                                    "ingredientRatio": 30.0, "productionTemperature": 120.0}]}},
            {"inputs": {"addRecipe": False, "deleteRecipe": False, "modifyRecipe": False,
                        "queryRecipe": True,
                        "recipeIn": {"recipeID": 1, "ingredientType": 0,
                                     "ingredientRatio": 0.0, "productionTemperature": 0.0}},
             "expect": {"recipeQueryResult": {"recipeID": 1, "ingredientType": 5,
                                              "ingredientRatio": 30.0, "productionTemperature": 120.0},
                        "error": False}},
        ]},
        {"id": "TC2", "description": "重复添加报错", "scan_ms": 10, "steps": [
            {"inputs": {"addRecipe": True, "deleteRecipe": False, "modifyRecipe": False,
                        "queryRecipe": False,
                        "recipeIn": {"recipeID": 1, "ingredientType": 5,
                                     "ingredientRatio": 30.0, "productionTemperature": 120.0}},
             "expect": {"recipeAdded": True, "error": False}},
            {"inputs": {"addRecipe": False, "deleteRecipe": False, "modifyRecipe": False,
                        "queryRecipe": False,
                        "recipeIn": {"recipeID": 1, "ingredientType": 5,
                                     "ingredientRatio": 30.0, "productionTemperature": 120.0}},
             "expect": {"recipeAdded": False, "error": False}},
            {"inputs": {"addRecipe": True, "deleteRecipe": False, "modifyRecipe": False,
                        "queryRecipe": False,
                        "recipeIn": {"recipeID": 1, "ingredientType": 9,
                                     "ingredientRatio": 50.0, "productionTemperature": 100.0}},
             "expect": {"recipeAdded": False, "error": True, "status": 32770}},
        ]},
    ],
    "reference": {
        "auto_wire": False,
        "duts": [
            {"name": "ST_Recipe", "kind": "struct",
             "declaration": "TYPE ST_Recipe :\nSTRUCT\n    recipeID : INT;\n    ingredientType : INT;\n    ingredientRatio : REAL;\n    productionTemperature : REAL;\nEND_STRUCT\nEND_TYPE\n"},
        ],
        "pous": [
            {
                "name": "RecipeMgmt",
                "kind": "function_block",
                "declaration": (
                    "FUNCTION_BLOCK RecipeMgmt\n"
                    "VAR_INPUT\n"
                    "    addRecipe : BOOL;\n"
                    "    deleteRecipe : BOOL;\n"
                    "    modifyRecipe : BOOL;\n"
                    "    queryRecipe : BOOL;\n"
                    "    recipeIn : ST_Recipe;\n"
                    "END_VAR\n"
                    "VAR_OUTPUT\n"
                    "    recipeAdded : BOOL;\n"
                    "    recipeDeleted : BOOL;\n"
                    "    recipeModified : BOOL;\n"
                    "    recipeQueryResult : ST_Recipe;\n"
                    "    error : BOOL;\n"
                    "    status : WORD;\n"
                    "END_VAR\n"
                    "VAR_IN_OUT\n"
                    "    recipe : ARRAY[1..10] OF ST_Recipe;\n"
                    "END_VAR\n"
                    "VAR\n"
                    "    i : INT;\n"
                    "    slot : INT;\n"
                    "    found : BOOL;\n"
                    "    addPrev : BOOL;\n"
                    "    delPrev : BOOL;\n"
                    "    modPrev : BOOL;\n"
                    "    qryPrev : BOOL;\n"
                    "END_VAR\n"),
                "implementation": (
                    "recipeAdded := FALSE;\n"
                    "recipeDeleted := FALSE;\n"
                    "recipeModified := FALSE;\n"
                    "error := FALSE;\n"
                    "status := 0;\n"
                    "IF queryRecipe AND NOT qryPrev THEN\n"
                    "    found := FALSE;\n"
                    "    FOR i := 1 TO 10 DO\n"
                    "        IF recipe[i].recipeID = recipeIn.recipeID THEN\n"
                    "            recipeQueryResult := recipe[i];\n"
                    "            found := TRUE;\n"
                    "        END_IF\n"
                    "    END_FOR\n"
                    "    IF NOT found THEN\n"
                    "        error := TRUE;\n"
                    "        status := 16#8001;\n"
                    "    END_IF\n"
                    "END_IF\n"
                    "IF addRecipe AND NOT addPrev THEN\n"
                    "    found := FALSE;\n"
                    "    FOR i := 1 TO 10 DO\n"
                    "        IF recipe[i].recipeID = recipeIn.recipeID THEN\n"
                    "            found := TRUE;\n"
                    "        END_IF\n"
                    "    END_FOR\n"
                    "    IF found THEN\n"
                    "        error := TRUE;\n"
                    "        status := 16#8002;\n"
                    "    ELSE\n"
                    "        slot := 0;\n"
                    "        FOR i := 1 TO 10 DO\n"
                    "            IF recipe[i].recipeID = 0 AND slot = 0 THEN\n"
                    "                slot := i;\n"
                    "            END_IF\n"
                    "        END_FOR\n"
                    "        IF slot = 0 THEN\n"
                    "            error := TRUE;\n"
                    "            status := 16#8003;\n"
                    "        ELSE\n"
                    "            recipe[slot] := recipeIn;\n"
                    "            recipeAdded := TRUE;\n"
                    "        END_IF\n"
                    "    END_IF\n"
                    "END_IF\n"
                    "IF deleteRecipe AND NOT delPrev THEN\n"
                    "    found := FALSE;\n"
                    "    FOR i := 1 TO 10 DO\n"
                    "        IF recipe[i].recipeID = recipeIn.recipeID THEN\n"
                    "            recipe[i].recipeID := 0;\n"
                    "            found := TRUE;\n"
                    "            recipeDeleted := TRUE;\n"
                    "        END_IF\n"
                    "    END_FOR\n"
                    "    IF NOT found THEN\n"
                    "        error := TRUE;\n"
                    "        status := 16#8004;\n"
                    "    END_IF\n"
                    "END_IF\n"
                    "IF modifyRecipe AND NOT modPrev THEN\n"
                    "    found := FALSE;\n"
                    "    FOR i := 1 TO 10 DO\n"
                    "        IF recipe[i].recipeID = recipeIn.recipeID THEN\n"
                    "            recipe[i] := recipeIn;\n"
                    "            found := TRUE;\n"
                    "            recipeModified := TRUE;\n"
                    "        END_IF\n"
                    "    END_FOR\n"
                    "    IF NOT found THEN\n"
                    "        error := TRUE;\n"
                    "        status := 16#8005;\n"
                    "    END_IF\n"
                    "END_IF\n"
                    "addPrev := addRecipe;\n"
                    "delPrev := deleteRecipe;\n"
                    "modPrev := modifyRecipe;\n"
                    "qryPrev := queryRecipe;\n"),
            },
            {
                "name": "PLC_PRG",
                "kind": "program",
                "declaration": (
                    "PROGRAM PLC_PRG\n"
                    "VAR\n"
                    "    fb : RecipeMgmt;\n"
                    "    db : ARRAY[1..10] OF ST_Recipe;\n"
                    "END_VAR\n"),
                "implementation": (
                    "fb(addRecipe := FALSE, deleteRecipe := FALSE, modifyRecipe := FALSE,\n"
                    "   queryRecipe := FALSE, recipeIn := db[1], recipe := db);\n"),
            },
        ],
    },
})

# ---------------------------------------------------------------------------
# hard 2: Material Proportioning Process Control
# ---------------------------------------------------------------------------
TASKS.append({
    "id": "public_hard_002",
    "source": "public",
    "difficulty": "hard",
    "title": "物料配比过程控制",
    "pou": {"type": "function_block", "name": "MaterialMix"},
    "requirement": {
        "en": (
            "Mix three materials and deliver through valve D. estop FALSE stops "
            "everything. Manual (opeMode FALSE): each valve/motor start button toggles "
            "its run on rising edge. Automatic (opeMode TRUE): autoStart opens valve A; "
            "level>=50 closes A opens B; level>=80 closes B; if processMode FALSE start "
            "mixing, on mixComplete stop and open D; if TRUE open C, level>=100 closes C "
            "then start mixing, on mixComplete stop and open D."
        ),
        "zh": (
            "混合三种物料并经阀 D 输送。estop 为 FALSE 时急停所有设备。手动(opeMode=FALSE)：各阀/电机"
            "启动按钮的上升沿切换对应运行状态。自动(opeMode=TRUE)：autoStart 后先开阀 A；液位≥50 关 A "
            "开 B；液位≥80 关 B；processMode=FALSE 则启动搅拌，mixComplete 后停搅拌开 D；processMode=TRUE "
            "则开 C，液位≥100 关 C 再启动搅拌，mixComplete 后停搅拌开 D。"
        ),
    },
    "interface": {
        "duts": [],
        "inputs": [
            {"name": "estop", "type": "BOOL", "desc": "FALSE 急停"},
            {"name": "opeMode", "type": "BOOL", "desc": "FALSE 手动 TRUE 自动"},
            {"name": "valveAStart", "type": "BOOL", "desc": "阀 A 启动按钮"},
            {"name": "valveBStart", "type": "BOOL", "desc": "阀 B 启动按钮"},
            {"name": "valveCStart", "type": "BOOL", "desc": "阀 C 启动按钮"},
            {"name": "valveDStart", "type": "BOOL", "desc": "阀 D 启动按钮"},
            {"name": "mixMotorStart", "type": "BOOL", "desc": "搅拌电机启动按钮"},
            {"name": "autoStart", "type": "BOOL", "desc": "自动启动按钮"},
            {"name": "processMode", "type": "BOOL", "desc": "工艺模式"},
            {"name": "levelSensor", "type": "INT", "desc": "液位(cm)"},
            {"name": "mixMotorComplete", "type": "BOOL", "desc": "搅拌完成信号"},
        ],
        "outputs": [
            {"name": "valveARun", "type": "BOOL", "desc": "阀 A 运行"},
            {"name": "valveBRun", "type": "BOOL", "desc": "阀 B 运行"},
            {"name": "valveCRun", "type": "BOOL", "desc": "阀 C 运行"},
            {"name": "valveDRun", "type": "BOOL", "desc": "阀 D 运行"},
            {"name": "mixMotorRun", "type": "BOOL", "desc": "搅拌电机运行"},
        ],
        "inouts": [],
    },
    "ltl_specs": [
        {"id": "P1", "description": "急停时所有设备停止。",
         "formula": "G(!estop -> (!valveARun && !valveBRun && !valveCRun && !valveDRun && !mixMotorRun))"},
        {"id": "P2", "description": "手动按钮上升沿切换阀门。",
         "formula": "G((!opeMode && estop && valveAStart && !X(valveAStart)) -> (valveARun <-> !X(valveARun)))"},
    ],
    "test_cases": [
        {"id": "TC1", "description": "手动切换", "scan_ms": 10, "steps": [
            {"inputs": {"estop": True, "opeMode": False, "valveAStart": False,
                        "valveBStart": False, "valveCStart": False, "valveDStart": False,
                        "mixMotorStart": False, "autoStart": False, "processMode": False,
                        "levelSensor": 0, "mixMotorComplete": False},
             "expect": {"valveARun": False}},
            {"inputs": {"estop": True, "opeMode": False, "valveAStart": True,
                        "valveBStart": False, "valveCStart": False, "valveDStart": False,
                        "mixMotorStart": False, "autoStart": False, "processMode": False,
                        "levelSensor": 0, "mixMotorComplete": False},
             "expect": {"valveARun": True}},
            {"inputs": {"estop": True, "opeMode": False, "valveAStart": False,
                        "valveBStart": False, "valveCStart": False, "valveDStart": False,
                        "mixMotorStart": False, "autoStart": False, "processMode": False,
                        "levelSensor": 0, "mixMotorComplete": False},
             "expect": {"valveARun": True}},
            {"inputs": {"estop": True, "opeMode": False, "valveAStart": True,
                        "valveBStart": False, "valveCStart": False, "valveDStart": False,
                        "mixMotorStart": False, "autoStart": False, "processMode": False,
                        "levelSensor": 0, "mixMotorComplete": False},
             "expect": {"valveARun": False}},
        ]},
        {"id": "TC2", "description": "急停关断所有设备", "scan_ms": 10, "steps": [
            {"inputs": {"estop": True, "opeMode": False, "valveAStart": True,
                        "valveBStart": False, "valveCStart": False, "valveDStart": False,
                        "mixMotorStart": False, "autoStart": False, "processMode": False,
                        "levelSensor": 0, "mixMotorComplete": False},
             "expect": {"valveARun": True}},
            {"inputs": {"estop": False, "opeMode": False, "valveAStart": False,
                        "valveBStart": False, "valveCStart": False, "valveDStart": False,
                        "mixMotorStart": False, "autoStart": False, "processMode": False,
                        "levelSensor": 0, "mixMotorComplete": False},
             "expect": {"valveARun": False, "valveBRun": False, "valveCRun": False,
                        "valveDRun": False, "mixMotorRun": False}},
        ]},
    ],
    "reference": {
        "duts": [],
        "pous": [{
            "name": "MaterialMix",
            "kind": "function_block",
            "declaration": (
                "FUNCTION_BLOCK MaterialMix\n"
                "VAR_INPUT\n"
                "    estop : BOOL;\n"
                "    opeMode : BOOL;\n"
                "    valveAStart : BOOL;\n"
                "    valveBStart : BOOL;\n"
                "    valveCStart : BOOL;\n"
                "    valveDStart : BOOL;\n"
                "    mixMotorStart : BOOL;\n"
                "    autoStart : BOOL;\n"
                "    processMode : BOOL;\n"
                "    levelSensor : INT;\n"
                "    mixMotorComplete : BOOL;\n"
                "END_VAR\n"
                "VAR_OUTPUT\n"
                "    valveARun : BOOL;\n"
                "    valveBRun : BOOL;\n"
                "    valveCRun : BOOL;\n"
                "    valveDRun : BOOL;\n"
                "    mixMotorRun : BOOL;\n"
                "END_VAR\n"
                "VAR\n"
                "    va : BOOL;\n"
                "    vb : BOOL;\n"
                "    vc : BOOL;\n"
                "    vd : BOOL;\n"
                "    mm : BOOL;\n"
                "    aPrev : BOOL;\n"
                "    bPrev : BOOL;\n"
                "    cPrev : BOOL;\n"
                "    dPrev : BOOL;\n"
                "    mPrev : BOOL;\n"
                "    autoStage : INT := 0;\n"
                "    autoStartPrev : BOOL;\n"
                "END_VAR\n"),
            "implementation": (
                "IF NOT estop THEN\n"
                "    va := FALSE;\n"
                "    vb := FALSE;\n"
                "    vc := FALSE;\n"
                "    vd := FALSE;\n"
                "    mm := FALSE;\n"
                "    autoStage := 0;\n"
                "ELSIF NOT opeMode THEN\n"
                "    IF valveAStart AND NOT aPrev THEN\n"
                "        va := NOT va;\n"
                "    END_IF\n"
                "    IF valveBStart AND NOT bPrev THEN\n"
                "        vb := NOT vb;\n"
                "    END_IF\n"
                "    IF valveCStart AND NOT cPrev THEN\n"
                "        vc := NOT vc;\n"
                "    END_IF\n"
                "    IF valveDStart AND NOT dPrev THEN\n"
                "        vd := NOT vd;\n"
                "    END_IF\n"
                "    IF mixMotorStart AND NOT mPrev THEN\n"
                "        mm := NOT mm;\n"
                "    END_IF\n"
                "    autoStage := 0;\n"
                "ELSE\n"
                "    va := FALSE;\n"
                "    vb := FALSE;\n"
                "    vc := FALSE;\n"
                "    vd := FALSE;\n"
                "    mm := FALSE;\n"
                "    CASE autoStage OF\n"
                "    0:\n"
                "        IF autoStart AND NOT autoStartPrev THEN\n"
                "            autoStage := 1;\n"
                "        END_IF\n"
                "    1:\n"
                "        va := TRUE;\n"
                "        IF levelSensor >= 50 THEN\n"
                "            autoStage := 2;\n"
                "        END_IF\n"
                "    2:\n"
                "        vb := TRUE;\n"
                "        IF levelSensor >= 80 THEN\n"
                "            IF processMode THEN\n"
                "                autoStage := 4;\n"
                "            ELSE\n"
                "                autoStage := 3;\n"
                "            END_IF\n"
                "        END_IF\n"
                "    3:\n"
                "        mm := TRUE;\n"
                "        IF mixMotorComplete THEN\n"
                "            autoStage := 5;\n"
                "        END_IF\n"
                "    4:\n"
                "        vc := TRUE;\n"
                "        IF levelSensor >= 100 THEN\n"
                "            autoStage := 3;\n"
                "        END_IF\n"
                "    5:\n"
                "        vd := TRUE;\n"
                "    END_CASE\n"
                "END_IF\n"
                "valveARun := va;\n"
                "valveBRun := vb;\n"
                "valveCRun := vc;\n"
                "valveDRun := vd;\n"
                "mixMotorRun := mm;\n"
                "aPrev := valveAStart;\n"
                "bPrev := valveBStart;\n"
                "cPrev := valveCStart;\n"
                "dPrev := valveDStart;\n"
                "mPrev := mixMotorStart;\n"
                "autoStartPrev := autoStart;\n"),
        }],
    },
})

# ---------------------------------------------------------------------------
# hard 3: Production Control (5 stations + weighing + temperature calc)
# ---------------------------------------------------------------------------
def _pc(mode=True, feed=False, wash=False, wsen=False, firing=False,
        output=False, wash_c=False, weight_c=False, w=150.0, firing_c=False):
    return {"Mode": mode, "ForwardButton": False, "ReverseButton": False,
            "SensorFeed": feed, "SensorWash": wash, "SensorWeight": wsen,
            "SensorFiring": firing, "SensorOutput": output,
            "washComplete": wash_c, "weightComplete": weight_c, "weight": w,
            "firingComplete": firing_c}


TASKS.append({
    "id": "public_hard_003",
    "source": "public",
    "difficulty": "hard",
    "title": "五工位生产控制",
    "pou": {"type": "function_block", "name": "ProductionControl"},
    "requirement": {
        "en": (
            "A line moves product through feed, wash, weigh, fire, output stations. "
            "Manual: forward/reverse interlocked. Automatic: SensorFeed starts forward "
            "to wash; SensorWash stops, washComplete forwards to weigh; SensorWeight "
            "stops, weightComplete judges 100..200 (else kick), qualified computes "
            "firingTemp 500..550 linear from weight 100..200 and forwards to fire; "
            "SensorFiring stops, firingComplete forwards to output; SensorOutput stops "
            "and lights CompletionLight until SensorOutput clears."
        ),
        "zh": (
            "生产线依次经过上料、清洗、称重、焙烧、成品五个工位。手动：正反转互锁。自动：SensorFeed "
            "触发正转送向清洗；SensorWash 停止，washComplete 后正转送向称重；SensorWeight 停止，"
            "weightComplete 后判定 100..200 合格(否则 kick 剔除)，合格则按重量 100..200 线性对应 "
            "500..550 计算 firingTemp 并正转送向焙烧；SensorFiring 停止，firingComplete 后正转送向"
            "成品；SensorOutput 停止并点亮 CompletionLight，直到 SensorOutput 消失熄灭。"
        ),
    },
    "interface": {
        "duts": [],
        "inputs": [
            {"name": "Mode", "type": "BOOL", "desc": "0 手动 1 自动"},
            {"name": "ForwardButton", "type": "BOOL", "desc": "正转按钮"},
            {"name": "ReverseButton", "type": "BOOL", "desc": "反转按钮"},
            {"name": "SensorFeed", "type": "BOOL", "desc": "上料检测"},
            {"name": "SensorWash", "type": "BOOL", "desc": "清洗检测"},
            {"name": "SensorWeight", "type": "BOOL", "desc": "称重检测"},
            {"name": "SensorFiring", "type": "BOOL", "desc": "焙烧检测"},
            {"name": "SensorOutput", "type": "BOOL", "desc": "成品检测"},
            {"name": "washComplete", "type": "BOOL", "desc": "清洗完成"},
            {"name": "weightComplete", "type": "BOOL", "desc": "称重完成"},
            {"name": "weight", "type": "REAL", "desc": "重量值"},
            {"name": "firingComplete", "type": "BOOL", "desc": "焙烧完成"},
        ],
        "outputs": [
            {"name": "MotorForward", "type": "BOOL", "desc": "正转"},
            {"name": "MotorReverse", "type": "BOOL", "desc": "反转"},
            {"name": "kick", "type": "BOOL", "desc": "剔除"},
            {"name": "CompletionLight", "type": "BOOL", "desc": "完成灯"},
            {"name": "firingTemp", "type": "REAL", "desc": "焙烧温度"},
        ],
        "inouts": [],
    },
    "ltl_specs": [
        {"id": "P1", "description": "正反转互锁。",
         "formula": "G(!(MotorForward && MotorReverse))"},
        {"id": "P2", "description": "完成灯只在成品位点亮。",
         "formula": "G(CompletionLight -> SensorOutput)"},
        {"id": "P3", "description": "焙烧温度在 500..550 内。",
         "formula": "G(firingTemp >= 500.0 && firingTemp <= 550.0)"},
    ],
    "test_cases": [
        {"id": "TC1", "description": "合格品焙烧温度计算(完整流程)", "scan_ms": 10, "steps": [
            {"inputs": _pc(feed=True), "expect": {}},
            {"inputs": _pc(), "expect": {"MotorForward": True}},
            {"inputs": _pc(wash=True), "expect": {"MotorForward": True}},
            {"inputs": _pc(wash=True, wash_c=True), "expect": {}},
            {"inputs": _pc(), "expect": {"MotorForward": True}},
            {"inputs": _pc(wsen=True), "expect": {"MotorForward": True}},
            {"inputs": _pc(wsen=True, weight_c=True, w=150.0),
             "expect": {"firingTemp": 525.0, "kick": False}},
        ]},
        {"id": "TC2", "description": "不合格品剔除(完整流程)", "scan_ms": 10, "steps": [
            {"inputs": _pc(feed=True), "expect": {}},
            {"inputs": _pc(), "expect": {"MotorForward": True}},
            {"inputs": _pc(wash=True), "expect": {"MotorForward": True}},
            {"inputs": _pc(wash=True, wash_c=True), "expect": {}},
            {"inputs": _pc(), "expect": {"MotorForward": True}},
            {"inputs": _pc(wsen=True), "expect": {"MotorForward": True}},
            {"inputs": _pc(wsen=True, weight_c=True, w=250.0),
             "expect": {"kick": True}},
        ]},
    ],
    "reference": {
        "duts": [],
        "pous": [{
            "name": "ProductionControl",
            "kind": "function_block",
            "declaration": (
                "FUNCTION_BLOCK ProductionControl\n"
                "VAR_INPUT\n"
                "    Mode : BOOL;\n"
                "    ForwardButton : BOOL;\n"
                "    ReverseButton : BOOL;\n"
                "    SensorFeed : BOOL;\n"
                "    SensorWash : BOOL;\n"
                "    SensorWeight : BOOL;\n"
                "    SensorFiring : BOOL;\n"
                "    SensorOutput : BOOL;\n"
                "    washComplete : BOOL;\n"
                "    weightComplete : BOOL;\n"
                "    weight : REAL;\n"
                "    firingComplete : BOOL;\n"
                "END_VAR\n"
                "VAR_OUTPUT\n"
                "    MotorForward : BOOL;\n"
                "    MotorReverse : BOOL;\n"
                "    kick : BOOL;\n"
                "    CompletionLight : BOOL;\n"
                "    firingTemp : REAL;\n"
                "END_VAR\n"
                "VAR\n"
                "    stage : INT := 0;\n"
                "END_VAR\n"),
            "implementation": (
                "MotorForward := FALSE;\n"
                "MotorReverse := FALSE;\n"
                "kick := FALSE;\n"
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
                "        IF SensorFeed THEN\n"
                "            stage := 1;\n"
                "        END_IF\n"
                "    1:\n"
                "        MotorForward := TRUE;\n"
                "        IF SensorWash THEN\n"
                "            stage := 2;\n"
                "        END_IF\n"
                "    2:\n"
                "        IF washComplete THEN\n"
                "            stage := 3;\n"
                "        END_IF\n"
                "    3:\n"
                "        MotorForward := TRUE;\n"
                "        IF SensorWeight THEN\n"
                "            stage := 4;\n"
                "        END_IF\n"
                "    4:\n"
                "        IF weightComplete THEN\n"
                "            IF weight >= 100.0 AND weight <= 200.0 THEN\n"
                "                firingTemp := 500.0 + (weight - 100.0) * 0.5;\n"
                "                stage := 5;\n"
                "            ELSE\n"
                "                kick := TRUE;\n"
                "                stage := 0;\n"
                "            END_IF\n"
                "        END_IF\n"
                "    5:\n"
                "        MotorForward := TRUE;\n"
                "        IF SensorFiring THEN\n"
                "            stage := 6;\n"
                "        END_IF\n"
                "    6:\n"
                "        IF firingComplete THEN\n"
                "            stage := 7;\n"
                "        END_IF\n"
                "    7:\n"
                "        MotorForward := TRUE;\n"
                "        IF SensorOutput THEN\n"
                "            stage := 8;\n"
                "        END_IF\n"
                "    8:\n"
                "        CompletionLight := TRUE;\n"
                "        IF NOT SensorOutput THEN\n"
                "            stage := 0;\n"
                "        END_IF\n"
                "    END_CASE\n"
                "END_IF\n"),
        }],
    },
})


# ---------------------------------------------------------------------------
# hard 4: Flexible Processing Control (process sequence conveyor)
# ---------------------------------------------------------------------------
TASKS.append({
    "id": "public_hard_004",
    "source": "public",
    "difficulty": "hard",
    "title": "柔性加工控制",
    "pou": {"type": "function_block", "name": "FlexProcess"},
    "requirement": {
        "en": (
            "A line has 5 stations (1 feed, 2..4 processing, 5 output). processSequence "
            "holds the station numbers each product visits; processLength 1..8 is the "
            "active length from processSequence[1], final entry is 5. At start (sensor1 "
            "+ station1Start) query the first sequence entry and move the conveyor to "
            "that station; on station2Complete..4Complete query the next entry and move "
            "accordingly until delivered to station 5."
        ),
        "zh": (
            "生产线有 5 个工位(1 上料、2..4 加工、5 成品)。processSequence 存储每个产品要经过的"
            "工位号；processLength 1..8 为有效长度，从 processSequence[1] 起，最后一项为 5。开始时"
            "(sensor1 且 station1Start) 查询第一个序列项并把输送带移到对应工位；收到 "
            "station2Complete..4Complete 后查询下一项并继续移动，直到送达 5 号工位。"
        ),
    },
    "interface": {
        "duts": [],
        "inputs": [
            {"name": "processLength", "type": "USINT", "desc": "有效序列长度 1..8"},
            {"name": "sensor1", "type": "BOOL", "desc": "1# 传感器"},
            {"name": "sensor2", "type": "BOOL", "desc": "2# 传感器"},
            {"name": "sensor3", "type": "BOOL", "desc": "3# 传感器"},
            {"name": "sensor4", "type": "BOOL", "desc": "4# 传感器"},
            {"name": "sensor5", "type": "BOOL", "desc": "5# 传感器"},
            {"name": "station1Start", "type": "BOOL", "desc": "1# 启动按钮"},
            {"name": "station2Complete", "type": "BOOL", "desc": "2# 加工完成"},
            {"name": "station3Complete", "type": "BOOL", "desc": "3# 加工完成"},
            {"name": "station4Complete", "type": "BOOL", "desc": "4# 加工完成"},
            {"name": "processSequence", "type": "ARRAY[1..8] OF USINT", "desc": "加工序列"},
        ],
        "outputs": [
            {"name": "conveyorLeft", "type": "BOOL", "desc": "输送带左转"},
            {"name": "conveyorRight", "type": "BOOL", "desc": "输送带右转"},
        ],
        "inouts": [],
    },
    "ltl_specs": [
        {"id": "P1", "description": "左右转互斥。",
         "formula": "G(!(conveyorLeft && conveyorRight))"},
        {"id": "P2", "description": "最终送达 5 号工位。",
         "formula": "G((sensor1 && station1Start) -> F(sensor5))"},
    ],
    "test_cases": [
        {"id": "TC1", "description": "按序列 1→2→4→5 移动", "scan_ms": 10, "steps": [
            {"inputs": {"processLength": 3, "sensor1": True, "sensor2": False,
                        "sensor3": False, "sensor4": False, "sensor5": False,
                        "station1Start": True, "station2Complete": False,
                        "station3Complete": False, "station4Complete": False,
                        "processSequence": [2, 4, 5, 0, 0, 0, 0, 0]},
             "expect": {}},
            {"inputs": {"processLength": 3, "sensor1": False, "sensor2": False,
                        "sensor3": False, "sensor4": False, "sensor5": False,
                        "station1Start": False, "station2Complete": False,
                        "station3Complete": False, "station4Complete": False,
                        "processSequence": [2, 4, 5, 0, 0, 0, 0, 0]},
             "expect": {"conveyorRight": True}},
            {"inputs": {"processLength": 3, "sensor1": False, "sensor2": True,
                        "sensor3": False, "sensor4": False, "sensor5": False,
                        "station1Start": False, "station2Complete": False,
                        "station3Complete": False, "station4Complete": False,
                        "processSequence": [2, 4, 5, 0, 0, 0, 0, 0]},
             "expect": {"conveyorRight": True}},
            {"inputs": {"processLength": 3, "sensor1": False, "sensor2": True,
                        "sensor3": False, "sensor4": False, "sensor5": False,
                        "station1Start": False, "station2Complete": True,
                        "station3Complete": False, "station4Complete": False,
                        "processSequence": [2, 4, 5, 0, 0, 0, 0, 0]},
             "expect": {}},
            {"inputs": {"processLength": 3, "sensor1": False, "sensor2": False,
                        "sensor3": False, "sensor4": False, "sensor5": False,
                        "station1Start": False, "station2Complete": False,
                        "station3Complete": False, "station4Complete": False,
                        "processSequence": [2, 4, 5, 0, 0, 0, 0, 0]},
             "expect": {"conveyorRight": True}},
        ]},
    ],
    "reference": {
        "duts": [],
        "pous": [{
            "name": "FlexProcess",
            "kind": "function_block",
            "declaration": (
                "FUNCTION_BLOCK FlexProcess\n"
                "VAR_INPUT\n"
                "    processLength : USINT;\n"
                "    sensor1 : BOOL;\n"
                "    sensor2 : BOOL;\n"
                "    sensor3 : BOOL;\n"
                "    sensor4 : BOOL;\n"
                "    sensor5 : BOOL;\n"
                "    station1Start : BOOL;\n"
                "    station2Complete : BOOL;\n"
                "    station3Complete : BOOL;\n"
                "    station4Complete : BOOL;\n"
                "    processSequence : ARRAY[1..8] OF USINT;\n"
                "END_VAR\n"
                "VAR_OUTPUT\n"
                "    conveyorLeft : BOOL;\n"
                "    conveyorRight : BOOL;\n"
                "END_VAR\n"
                "VAR\n"
                "    stage : INT := 0;\n"
                "    seqIdx : USINT;\n"
                "    current : USINT;\n"
                "    target : USINT;\n"
                "END_VAR\n"),
            "implementation": (
                "conveyorLeft := FALSE;\n"
                "conveyorRight := FALSE;\n"
                "CASE stage OF\n"
                "0:\n"
                "    IF sensor1 AND station1Start THEN\n"
                "        seqIdx := 1;\n"
                "        current := 1;\n"
                "        stage := 1;\n"
                "    END_IF\n"
                "1:\n"
                "    target := processSequence[seqIdx];\n"
                "    IF target > current THEN\n"
                "        conveyorRight := TRUE;\n"
                "    ELSIF target < current THEN\n"
                "        conveyorLeft := TRUE;\n"
                "    END_IF\n"
                "    IF (target = 1 AND sensor1) OR (target = 2 AND sensor2)\n"
                "        OR (target = 3 AND sensor3) OR (target = 4 AND sensor4)\n"
                "        OR (target = 5 AND sensor5) THEN\n"
                "        current := target;\n"
                "        IF target = 5 THEN\n"
                "            stage := 3;\n"
                "        ELSE\n"
                "            stage := 2;\n"
                "        END_IF\n"
                "    END_IF\n"
                "2:\n"
                "    IF (current = 2 AND station2Complete)\n"
                "        OR (current = 3 AND station3Complete)\n"
                "        OR (current = 4 AND station4Complete) THEN\n"
                "        seqIdx := seqIdx + 1;\n"
                "        stage := 1;\n"
                "    END_IF\n"
                "3:\n"
                "END_CASE\n"),
        }],
    },
})

# ---------------------------------------------------------------------------
# hard 5: Mechanical Arm Control (4 modes)
# ---------------------------------------------------------------------------
TASKS.append({
    "id": "public_hard_005",
    "source": "public",
    "difficulty": "hard",
    "title": "机械臂控制",
    "pou": {"type": "function_block", "name": "MechArm"},
    "requirement": {
        "en": (
            "Control an arm with six actions (down/up/left/right/grip/release) and four "
            "mutually-exclusive modes. Manual: each button moves its axis while the "
            "corresponding limit switch is off. Single-step: each Start press runs one "
            "preset action until its limit. Single-cycle: Start runs the full cycle "
            "down-grip-up-right-down-release-up-left. Continuous: Start repeats the "
            "cycle. Emergency stop stops everything."
        ),
        "zh": (
            "控制一个六动作(下/上/左/右/抓/放)机械臂，四种互斥模式。手动：各按钮在对应限位未到位时"
            "驱动对应动作。单步：每次按 Start 执行一个预设动作直至到位。单周期：按 Start 执行完整周期"
            "下-抓-上-右-下-放-上-左。连续：按 Start 后循环执行。急停可随时停止所有动作。"
        ),
    },
    "interface": {
        "duts": [],
        "inputs": [
            {"name": "ManualMode", "type": "BOOL", "desc": "手动模式"},
            {"name": "SingleStepMode", "type": "BOOL", "desc": "单步模式"},
            {"name": "SingleCycleMode", "type": "BOOL", "desc": "单周期模式"},
            {"name": "ContinuousMode", "type": "BOOL", "desc": "连续模式"},
            {"name": "EmergencyStop", "type": "BOOL", "desc": "FALSE 急停"},
            {"name": "Start", "type": "BOOL", "desc": "启动"},
            {"name": "DownButton", "type": "BOOL", "desc": "下降按钮"},
            {"name": "UpButton", "type": "BOOL", "desc": "上升按钮"},
            {"name": "LeftButton", "type": "BOOL", "desc": "左移按钮"},
            {"name": "RightButton", "type": "BOOL", "desc": "右移按钮"},
            {"name": "GripButton", "type": "BOOL", "desc": "抓取按钮"},
            {"name": "ReleaseButton", "type": "BOOL", "desc": "释放按钮"},
            {"name": "DownLimitSwitch", "type": "BOOL", "desc": "下降到位"},
            {"name": "UpLimitSwitch", "type": "BOOL", "desc": "上升到位"},
            {"name": "LeftLimitSwitch", "type": "BOOL", "desc": "左移到位"},
            {"name": "RightLimitSwitch", "type": "BOOL", "desc": "右移到位"},
            {"name": "GripLimitSwitch", "type": "BOOL", "desc": "抓取到位"},
            {"name": "ReleaseLimitSwitch", "type": "BOOL", "desc": "释放到位"},
        ],
        "outputs": [
            {"name": "MoveDown", "type": "BOOL", "desc": "下降命令"},
            {"name": "MoveUp", "type": "BOOL", "desc": "上升命令"},
            {"name": "MoveLeft", "type": "BOOL", "desc": "左移命令"},
            {"name": "MoveRight", "type": "BOOL", "desc": "右移命令"},
            {"name": "ActivateGrip", "type": "BOOL", "desc": "抓取命令"},
            {"name": "ActivateRelease", "type": "BOOL", "desc": "释放命令"},
        ],
        "inouts": [],
    },
    "ltl_specs": [
        {"id": "P1", "description": "急停时所有动作停止。",
         "formula": "G(!EmergencyStop -> (!MoveDown && !MoveUp && !MoveLeft && !MoveRight && !ActivateGrip && !ActivateRelease))"},
    ],
    "test_cases": [
        {"id": "TC1", "description": "手动模式按钮驱动与到位停止", "scan_ms": 10, "steps": [
            {"inputs": {"ManualMode": True, "SingleStepMode": False, "SingleCycleMode": False,
                        "ContinuousMode": False, "EmergencyStop": True, "Start": False,
                        "DownButton": True, "UpButton": False, "LeftButton": False,
                        "RightButton": False, "GripButton": False, "ReleaseButton": False,
                        "DownLimitSwitch": False, "UpLimitSwitch": True, "LeftLimitSwitch": True,
                        "RightLimitSwitch": True, "GripLimitSwitch": True, "ReleaseLimitSwitch": True},
             "expect": {"MoveDown": True}},
            {"inputs": {"ManualMode": True, "SingleStepMode": False, "SingleCycleMode": False,
                        "ContinuousMode": False, "EmergencyStop": True, "Start": False,
                        "DownButton": True, "UpButton": False, "LeftButton": False,
                        "RightButton": False, "GripButton": False, "ReleaseButton": False,
                        "DownLimitSwitch": True, "UpLimitSwitch": True, "LeftLimitSwitch": True,
                        "RightLimitSwitch": True, "GripLimitSwitch": True, "ReleaseLimitSwitch": True},
             "expect": {"MoveDown": False}},
        ]},
        {"id": "TC2", "description": "急停停止所有动作", "scan_ms": 10, "steps": [
            {"inputs": {"ManualMode": False, "SingleStepMode": True, "SingleCycleMode": False,
                        "ContinuousMode": False, "EmergencyStop": False, "Start": False,
                        "DownButton": False, "UpButton": False, "LeftButton": False,
                        "RightButton": False, "GripButton": False, "ReleaseButton": False,
                        "DownLimitSwitch": False, "UpLimitSwitch": True, "LeftLimitSwitch": True,
                        "RightLimitSwitch": True, "GripLimitSwitch": True, "ReleaseLimitSwitch": True},
             "expect": {"MoveDown": False, "MoveUp": False, "MoveLeft": False, "MoveRight": False,
                        "ActivateGrip": False, "ActivateRelease": False}},
        ]},
    ],
    "reference": {
        "duts": [],
        "pous": [{
            "name": "MechArm",
            "kind": "function_block",
            "declaration": (
                "FUNCTION_BLOCK MechArm\n"
                "VAR_INPUT\n"
                "    ManualMode : BOOL;\n"
                "    SingleStepMode : BOOL;\n"
                "    SingleCycleMode : BOOL;\n"
                "    ContinuousMode : BOOL;\n"
                "    EmergencyStop : BOOL;\n"
                "    Start : BOOL;\n"
                "    DownButton : BOOL;\n"
                "    UpButton : BOOL;\n"
                "    LeftButton : BOOL;\n"
                "    RightButton : BOOL;\n"
                "    GripButton : BOOL;\n"
                "    ReleaseButton : BOOL;\n"
                "    DownLimitSwitch : BOOL;\n"
                "    UpLimitSwitch : BOOL;\n"
                "    LeftLimitSwitch : BOOL;\n"
                "    RightLimitSwitch : BOOL;\n"
                "    GripLimitSwitch : BOOL;\n"
                "    ReleaseLimitSwitch : BOOL;\n"
                "END_VAR\n"
                "VAR_OUTPUT\n"
                "    MoveDown : BOOL;\n"
                "    MoveUp : BOOL;\n"
                "    MoveLeft : BOOL;\n"
                "    MoveRight : BOOL;\n"
                "    ActivateGrip : BOOL;\n"
                "    ActivateRelease : BOOL;\n"
                "END_VAR\n"
                "VAR\n"
                "    step : INT := 0;\n"
                "    executing : BOOL;\n"
                "    startPrev : BOOL;\n"
                "    startEdge : BOOL;\n"
                "END_VAR\n"),
            "implementation": (
                "MoveDown := FALSE;\n"
                "MoveUp := FALSE;\n"
                "MoveLeft := FALSE;\n"
                "MoveRight := FALSE;\n"
                "ActivateGrip := FALSE;\n"
                "ActivateRelease := FALSE;\n"
                "IF NOT EmergencyStop THEN\n"
                "    executing := FALSE;\n"
                "    step := 0;\n"
                "ELSIF ManualMode THEN\n"
                "    MoveDown := DownButton AND NOT DownLimitSwitch;\n"
                "    MoveUp := UpButton AND NOT UpLimitSwitch;\n"
                "    MoveLeft := LeftButton AND NOT LeftLimitSwitch;\n"
                "    MoveRight := RightButton AND NOT RightLimitSwitch;\n"
                "    ActivateGrip := GripButton AND NOT GripLimitSwitch;\n"
                "    ActivateRelease := ReleaseButton AND NOT ReleaseLimitSwitch;\n"
                "    step := 0;\n"
                "ELSE\n"
                "    startEdge := Start AND NOT startPrev;\n"
                "    IF startEdge THEN\n"
                "        executing := TRUE;\n"
                "        IF step >= 8 THEN\n"
                "            step := 0;\n"
                "        END_IF\n"
                "    END_IF\n"
                "    CASE step OF\n"
                "    0:\n"
                "        IF executing THEN\n"
                "            MoveDown := TRUE;\n"
                "            IF DownLimitSwitch THEN\n"
                "                IF SingleStepMode THEN executing := FALSE; END_IF\n"
                "                step := 1;\n"
                "            END_IF\n"
                "        END_IF\n"
                "    1:\n"
                "        IF executing THEN\n"
                "            ActivateGrip := TRUE;\n"
                "            IF GripLimitSwitch THEN\n"
                "                IF SingleStepMode THEN executing := FALSE; END_IF\n"
                "                step := 2;\n"
                "            END_IF\n"
                "        END_IF\n"
                "    2:\n"
                "        IF executing THEN\n"
                "            MoveUp := TRUE;\n"
                "            IF UpLimitSwitch THEN\n"
                "                IF SingleStepMode THEN executing := FALSE; END_IF\n"
                "                step := 3;\n"
                "            END_IF\n"
                "        END_IF\n"
                "    3:\n"
                "        IF executing THEN\n"
                "            MoveRight := TRUE;\n"
                "            IF RightLimitSwitch THEN\n"
                "                IF SingleStepMode THEN executing := FALSE; END_IF\n"
                "                step := 4;\n"
                "            END_IF\n"
                "        END_IF\n"
                "    4:\n"
                "        IF executing THEN\n"
                "            MoveDown := TRUE;\n"
                "            IF DownLimitSwitch THEN\n"
                "                IF SingleStepMode THEN executing := FALSE; END_IF\n"
                "                step := 5;\n"
                "            END_IF\n"
                "        END_IF\n"
                "    5:\n"
                "        IF executing THEN\n"
                "            ActivateRelease := TRUE;\n"
                "            IF ReleaseLimitSwitch THEN\n"
                "                IF SingleStepMode THEN executing := FALSE; END_IF\n"
                "                step := 6;\n"
                "            END_IF\n"
                "        END_IF\n"
                "    6:\n"
                "        IF executing THEN\n"
                "            MoveUp := TRUE;\n"
                "            IF UpLimitSwitch THEN\n"
                "                IF SingleStepMode THEN executing := FALSE; END_IF\n"
                "                step := 7;\n"
                "            END_IF\n"
                "        END_IF\n"
                "    7:\n"
                "        IF executing THEN\n"
                "            MoveLeft := TRUE;\n"
                "            IF LeftLimitSwitch THEN\n"
                "                IF SingleStepMode THEN\n"
                "                    executing := FALSE;\n"
                "                    step := 0;\n"
                "                ELSIF SingleCycleMode THEN\n"
                "                    executing := FALSE;\n"
                "                    step := 8;\n"
                "                ELSE\n"
                "                    step := 0;\n"
                "                END_IF\n"
                "            END_IF\n"
                "        END_IF\n"
                "    END_CASE\n"
                "END_IF\n"
                "startPrev := Start;\n"),
        }],
    },
})


# ---------------------------------------------------------------------------
# hard 6: FIFO queue (adapted from VARIANT to INT element)
# ---------------------------------------------------------------------------
TASKS.append({
    "id": "public_hard_006",
    "source": "public",
    "difficulty": "hard",
    "title": "FIFO 先进先出队列",
    "pou": {"type": "function_block", "name": "FifoQueue"},
    "requirement": {
        "en": (
            "Implement a first-in-first-out circular queue whose capacity is derived "
            "from the caller-supplied buffer. enqueue rising edge appends item at the "
            "tail if not full; dequeue rising edge removes the front into item if not "
            "empty; reset empties the queue. status: 0 ok, 16#8001 dequeue empty, "
            "16#8002 enqueue full. (Adapted: element type fixed to INT, capacity "
            "derived from the buffer bounds.)"
        ),
        "zh": (
            "实现先进先出环形队列，容量由调用方提供的缓冲推导。enqueue 上升沿在队尾追加 item(未满时)；"
            "dequeue 上升沿把队首元素写回 item(非空时)；reset 清空队列。status：0 成功、16#8001 空队列"
            "出队、16#8002 满队列入队。(改编：原题用 VARIANT 泛型，因编译服务不支持 VARIANT，元素类型"
            "固定为 INT，容量仍由缓冲下界/上界推导。)"
        ),
    },
    "interface": {
        "duts": [],
        "inputs": [
            {"name": "enqueue", "type": "BOOL", "desc": "入队请求(上升沿一次)"},
            {"name": "dequeue", "type": "BOOL", "desc": "出队请求(上升沿一次)"},
            {"name": "reset", "type": "BOOL", "desc": "清空队列(优先)"},
        ],
        "outputs": [
            {"name": "elementCount", "type": "DINT", "desc": "当前有效元素数"},
            {"name": "status", "type": "WORD", "desc": "0 正常 8001 空出队 8002 满入队"},
        ],
        "inouts": [
            {"name": "item", "type": "INT", "desc": "入队取值/出队写回"},
            {"name": "buffer", "type": "ARRAY[*] OF INT", "desc": "队列存储", "capacity": 10},
        ],
    },
    "meta": {
        "adaptation": "原题 buffer/item 为 VARIANT 泛型引用；编译服务(CODESYS 脚本工程)中 VARIANT 为未知类型，故改编为 INT 元素 + ARRAY[*] 定长缓冲，容量仍由实参下界/上界推导，队列逻辑不变。"
    },
    "ltl_specs": [
        {"id": "P1", "description": "元素数不越界。",
         "formula": "G(elementCount >= 0 && elementCount <= 10)"},
        {"id": "P2", "description": "空队列出队报 8001。",
         "formula": "G((reset || elementCount = 0) -> (status = 0 || status = 16#8001))"},
    ],
    "test_cases": [
        {"id": "TC1", "description": "入队与出队", "scan_ms": 10, "steps": [
            {"inputs": {"enqueue": False, "dequeue": False, "reset": True, "item": 0},
             "expect": {"elementCount": 0, "status": 0}},
            {"inputs": {"enqueue": True, "dequeue": False, "reset": False, "item": 5},
             "expect": {"elementCount": 1, "status": 0, "buffer": [5]}},
            {"inputs": {"enqueue": False, "dequeue": False, "reset": False, "item": 7},
             "expect": {"elementCount": 1, "status": 0}},
            {"inputs": {"enqueue": True, "dequeue": False, "reset": False, "item": 7},
             "expect": {"elementCount": 2, "status": 0}},
            {"inputs": {"enqueue": False, "dequeue": True, "reset": False, "item": 0},
             "expect": {"elementCount": 1, "status": 0, "item": 5}},
        ]},
        {"id": "TC2", "description": "空队列出队报错", "scan_ms": 10, "steps": [
            {"inputs": {"enqueue": False, "dequeue": False, "reset": True, "item": 0},
             "expect": {"elementCount": 0}},
            {"inputs": {"enqueue": False, "dequeue": True, "reset": False, "item": 0},
             "expect": {"elementCount": 0, "status": 32769}},
        ]},
    ],
    "reference": {
        "auto_wire": False,
        "duts": [],
        "pous": [
            {
                "name": "FifoQueue",
                "kind": "function_block",
                "declaration": (
                    "FUNCTION_BLOCK FifoQueue\n"
                    "VAR_INPUT\n"
                    "    enqueue : BOOL;\n"
                    "    dequeue : BOOL;\n"
                    "    reset : BOOL;\n"
                    "END_VAR\n"
                    "VAR_OUTPUT\n"
                    "    elementCount : DINT;\n"
                    "    status : WORD;\n"
                    "END_VAR\n"
                    "VAR_IN_OUT\n"
                    "    item : INT;\n"
                    "    buffer : ARRAY[*] OF INT;\n"
                    "END_VAR\n"
                    "VAR\n"
                    "    head : DINT := 0;\n"
                    "    tail : DINT := 0;\n"
                    "    count : DINT := 0;\n"
                    "    capacity : DINT;\n"
                    "    enqPrev : BOOL;\n"
                    "    deqPrev : BOOL;\n"
                    "    enqRising : BOOL;\n"
                    "    deqRising : BOOL;\n"
                    "END_VAR\n"),
                "implementation": (
                    "capacity := UPPER_BOUND(buffer, 1) - LOWER_BOUND(buffer, 1) + 1;\n"
                    "status := 0;\n"
                    "enqRising := enqueue AND NOT enqPrev;\n"
                    "deqRising := dequeue AND NOT deqPrev;\n"
                    "enqPrev := enqueue;\n"
                    "deqPrev := dequeue;\n"
                    "IF reset THEN\n"
                    "    head := 0;\n"
                    "    tail := 0;\n"
                    "    count := 0;\n"
                    "ELSIF enqRising THEN\n"
                    "    IF count >= capacity THEN\n"
                    "        status := 16#8002;\n"
                    "    ELSE\n"
                    "        buffer[LOWER_BOUND(buffer, 1) + tail] := item;\n"
                    "        tail := tail + 1;\n"
                    "        IF tail >= capacity THEN\n"
                    "            tail := 0;\n"
                    "        END_IF\n"
                    "        count := count + 1;\n"
                    "    END_IF\n"
                    "ELSIF deqRising THEN\n"
                    "    IF count <= 0 THEN\n"
                    "        status := 16#8001;\n"
                    "    ELSE\n"
                    "        item := buffer[LOWER_BOUND(buffer, 1) + head];\n"
                    "        head := head + 1;\n"
                    "        IF head >= capacity THEN\n"
                    "            head := 0;\n"
                    "        END_IF\n"
                    "        count := count - 1;\n"
                    "    END_IF\n"
                    "END_IF\n"
                    "elementCount := count;\n"),
            },
            {
                "name": "PLC_PRG",
                "kind": "program",
                "declaration": (
                    "PROGRAM PLC_PRG\n"
                    "VAR\n"
                    "    fb : FifoQueue;\n"
                    "    buf : ARRAY[1..10] OF INT;\n"
                    "    it : INT;\n"
                    "END_VAR\n"),
                "implementation": (
                    "fb(enqueue := FALSE, dequeue := FALSE, reset := FALSE, item := it, buffer := buf);\n"),
            },
        ],
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
