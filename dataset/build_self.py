"""Build self-authored task files.

10 self-built questions (3 easy / 4 medium / 3 hard) across discrete-logic,
process, motion and logic scenarios. Each has a meta block recording the
scenario rationale (来源/合理性/多样性). Reference ST must compile.

Run:  python dataset/build_self.py
"""
import json
import os

import tc_annotations  # noqa: E402  (dataset/tc_annotations.py)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tasks")

TASKS = []


def _t(**kw):
    TASKS.append(kw)


# ---------------------------------------------------------------------------
# easy 1: traffic light (two-phase, timer toggle)
# ---------------------------------------------------------------------------
_t(
    id="self_easy_001", source="self_built", difficulty="easy",
    title="两相交通信号灯", pou={"type": "function_block", "name": "TrafficLight"},
    requirement={
        "zh": "实现一个两相交通信号灯：南北绿灯亮 5 秒、东西绿灯亮 5 秒，两方向交替，"
              "任意时刻至多一个方向为绿灯。",
        "en": "A two-phase traffic light: north-south green for 5s, east-west green "
              "for 5s, alternating; at most one direction is green at any time.",
    },
    interface={
        "duts": [], "inouts": [],
        "inputs": [],
        "outputs": [
            {"name": "NS_Green", "type": "BOOL", "desc": "南北绿灯"},
            {"name": "EW_Green", "type": "BOOL", "desc": "东西绿灯"},
        ],
    },
    meta={"scenario": "离散逻辑/定时器；改编自常见交通灯控制题，考查自复位定时器与相位切换。"},
    ltl_specs=[
        {"id": "P1", "description": "两方向绿灯互斥。",
         "formula": "G(!(NS_Green && EW_Green))"},
        {"id": "P2", "description": "至少一个方向为绿灯。",
         "formula": "G(NS_Green || EW_Green)"},
    ],
    test_cases=[
        {"id": "TC1", "description": "相位交替", "scan_ms": 1000, "steps": [
            {"inputs": {}, "expect": {"NS_Green": True, "EW_Green": False}},
            {"inputs": {}, "repeat": 5, "expect": {"NS_Green": True, "EW_Green": False}},
            {"inputs": {}, "repeat": 1, "expect": {"NS_Green": False, "EW_Green": True}},
            {"inputs": {}, "repeat": 5, "expect": {"NS_Green": False, "EW_Green": True}},
            {"inputs": {}, "repeat": 1, "expect": {"NS_Green": True, "EW_Green": False}},
        ]},
    ],
    reference={"duts": [], "pous": [{
        "name": "TrafficLight", "kind": "function_block",
        "declaration": (
            "FUNCTION_BLOCK TrafficLight\n"
            "VAR_OUTPUT\n    NS_Green : BOOL;\n    EW_Green : BOOL;\nEND_VAR\n"
            "VAR\n    phase : INT := 0;\n    timer : TON;\nEND_VAR\n"),
        "implementation": (
            "IF phase = 0 THEN\n"
            "    NS_Green := TRUE;\n"
            "    EW_Green := FALSE;\n"
            "ELSE\n"
            "    NS_Green := FALSE;\n"
            "    EW_Green := TRUE;\n"
            "END_IF\n"
            "timer(IN := TRUE, PT := T#5s);\n"
            "IF timer.Q THEN\n"
            "    phase := 1 - phase;\n"
            "    timer(IN := FALSE);\n"
            "END_IF\n"),
    }]},
)

# ---------------------------------------------------------------------------
# easy 2: tank level pump control with high-high alarm
# ---------------------------------------------------------------------------
_t(
    id="self_easy_002", source="self_built", difficulty="easy",
    title="水箱液位控制与高高报警", pou={"type": "function_block", "name": "TankLevel"},
    requirement={
        "zh": "控制水箱：液位低于 lowLevel 时启动水泵，高于 highLevel 时停止水泵(滞环)；"
              "液位超过 highHighLevel 时输出高高报警。",
        "en": "Control a tank: start the pump when level drops below lowLevel, stop it "
              "when level rises above highLevel (hysteresis); alarm when level exceeds "
              "highHighLevel.",
    },
    interface={
        "duts": [], "inouts": [],
        "inputs": [
            {"name": "level", "type": "REAL", "desc": "液位"},
            {"name": "lowLevel", "type": "REAL", "desc": "低液位启动点"},
            {"name": "highLevel", "type": "REAL", "desc": "高液位停止点"},
            {"name": "highHighLevel", "type": "REAL", "desc": "高高报警点"},
        ],
        "outputs": [
            {"name": "pumpOn", "type": "BOOL", "desc": "水泵运行"},
            {"name": "highHighAlarm", "type": "BOOL", "desc": "高高报警"},
        ],
    },
    meta={"scenario": "流程行业液位控制，带滞环与超限报警，考查滞环保持逻辑。"},
    ltl_specs=[
        {"id": "P1", "description": "超过高高报警点必须报警。",
         "formula": "G(level > highHighLevel -> highHighAlarm)"},
        {"id": "P2", "description": "低于启动点启动水泵。",
         "formula": "G(level < lowLevel -> pumpOn)"},
    ],
    test_cases=[
        {"id": "TC1", "description": "滞环启停", "scan_ms": 10, "steps": [
            {"inputs": {"level": 5.0, "lowLevel": 10.0, "highLevel": 20.0, "highHighLevel": 25.0},
             "expect": {"pumpOn": True, "highHighAlarm": False}},
            {"inputs": {"level": 15.0, "lowLevel": 10.0, "highLevel": 20.0, "highHighLevel": 25.0},
             "expect": {"pumpOn": True, "highHighAlarm": False}},
            {"inputs": {"level": 22.0, "lowLevel": 10.0, "highLevel": 20.0, "highHighLevel": 25.0},
             "expect": {"pumpOn": False, "highHighAlarm": False}},
        ]},
        {"id": "TC2", "description": "高高报警", "scan_ms": 10, "steps": [
            {"inputs": {"level": 26.0, "lowLevel": 10.0, "highLevel": 20.0, "highHighLevel": 25.0},
             "expect": {"highHighAlarm": True, "pumpOn": False}},
        ]},
    ],
    reference={"duts": [], "pous": [{
        "name": "TankLevel", "kind": "function_block",
        "declaration": (
            "FUNCTION_BLOCK TankLevel\n"
            "VAR_INPUT\n    level : REAL;\n    lowLevel : REAL;\n    highLevel : REAL;\n"
            "    highHighLevel : REAL;\nEND_VAR\n"
            "VAR_OUTPUT\n    pumpOn : BOOL;\n    highHighAlarm : BOOL;\nEND_VAR\n"),
        "implementation": (
            "IF level < lowLevel THEN\n    pumpOn := TRUE;\n"
            "ELSIF level > highLevel THEN\n    pumpOn := FALSE;\nEND_IF\n"
            "highHighAlarm := (level > highHighLevel);\n"),
    }]},
)

# ---------------------------------------------------------------------------
# easy 3: automatic door
# ---------------------------------------------------------------------------
_t(
    id="self_easy_003", source="self_built", difficulty="easy",
    title="自动门控制", pou={"type": "function_block", "name": "AutoDoor"},
    requirement={
        "zh": "控制自动门：感应到人时开门，完全开启后保持 3 秒再关门；关门过程中若再次感应到人"
              "或检测到障碍物则重新开门。",
        "en": "Control an automatic door: open on presence, hold 3s after fully open, "
              "then close; if presence or an obstacle is detected while closing, reopen.",
    },
    interface={
        "duts": [], "inouts": [],
        "inputs": [
            {"name": "presence", "type": "BOOL", "desc": "有人感应"},
            {"name": "openLimit", "type": "BOOL", "desc": "开到位"},
            {"name": "closeLimit", "type": "BOOL", "desc": "关到位"},
            {"name": "obstacle", "type": "BOOL", "desc": "障碍物"},
        ],
        "outputs": [
            {"name": "openCmd", "type": "BOOL", "desc": "开门命令"},
            {"name": "closeCmd", "type": "BOOL", "desc": "关门命令"},
        ],
    },
    meta={"scenario": "门控/离散逻辑，含延时与障碍物重开，考查状态机与定时器。"},
    ltl_specs=[
        {"id": "P1", "description": "开门与关门互斥。",
         "formula": "G(!(openCmd && closeCmd))"},
        {"id": "P2", "description": "有人时开门。",
         "formula": "G(presence -> openCmd)"},
    ],
    test_cases=[
        {"id": "TC1", "description": "开门保持后关门", "scan_ms": 1000, "steps": [
            {"inputs": {"presence": True, "openLimit": False, "closeLimit": False, "obstacle": False},
             "expect": {"openCmd": False, "closeCmd": False}},
            {"inputs": {"presence": False, "openLimit": True, "closeLimit": False, "obstacle": False},
             "expect": {"openCmd": True, "closeCmd": False}},
            {"inputs": {"presence": False, "openLimit": True, "closeLimit": False, "obstacle": False},
             "repeat": 3, "expect": {"openCmd": False, "closeCmd": False}},
            {"inputs": {"presence": False, "openLimit": True, "closeLimit": False, "obstacle": False},
             "repeat": 1, "expect": {"openCmd": False, "closeCmd": False}},
            {"inputs": {"presence": False, "openLimit": True, "closeLimit": False, "obstacle": False},
             "repeat": 1, "expect": {"openCmd": False, "closeCmd": True}},
        ]},
        {"id": "TC2", "description": "关门遇障碍重开", "scan_ms": 1000, "steps": [
            {"inputs": {"presence": True, "openLimit": False, "closeLimit": False, "obstacle": False},
             "expect": {"openCmd": False, "closeCmd": False}},
            {"inputs": {"presence": False, "openLimit": True, "closeLimit": False, "obstacle": False},
             "expect": {"openCmd": True, "closeCmd": False}},
            {"inputs": {"presence": False, "openLimit": True, "closeLimit": False, "obstacle": False},
             "repeat": 3, "expect": {"openCmd": False, "closeCmd": False}},
            {"inputs": {"presence": False, "openLimit": True, "closeLimit": False, "obstacle": False},
             "repeat": 1, "expect": {"openCmd": False, "closeCmd": False}},
            {"inputs": {"presence": False, "openLimit": True, "closeLimit": False, "obstacle": False},
             "repeat": 1, "expect": {"openCmd": False, "closeCmd": True}},
            {"inputs": {"presence": False, "openLimit": True, "closeLimit": False, "obstacle": True},
             "expect": {"openCmd": False, "closeCmd": True}},
            {"inputs": {"presence": False, "openLimit": True, "closeLimit": False, "obstacle": False},
             "expect": {"openCmd": True, "closeCmd": False}},
        ]},
    ],
    reference={"duts": [], "pous": [{
        "name": "AutoDoor", "kind": "function_block",
        "declaration": (
            "FUNCTION_BLOCK AutoDoor\n"
            "VAR_INPUT\n    presence : BOOL;\n    openLimit : BOOL;\n    closeLimit : BOOL;\n"
            "    obstacle : BOOL;\nEND_VAR\n"
            "VAR_OUTPUT\n    openCmd : BOOL;\n    closeCmd : BOOL;\nEND_VAR\n"
            "VAR\n    stage : INT := 0;\n    hold : TON;\nEND_VAR\n"),
        "implementation": (
            "openCmd := FALSE;\n"
            "closeCmd := FALSE;\n"
            "CASE stage OF\n"
            "0:\n"
            "    IF presence THEN\n"
            "        stage := 1;\n"
            "    END_IF\n"
            "1:\n"
            "    openCmd := TRUE;\n"
            "    IF openLimit THEN\n"
            "        stage := 2;\n"
            "    END_IF\n"
            "2:\n"
            "    IF presence OR obstacle THEN\n"
            "        stage := 1;\n"
            "    ELSE\n"
            "        hold(IN := TRUE, PT := T#3s);\n"
            "        IF hold.Q THEN\n"
            "            stage := 3;\n"
            "        END_IF\n"
            "    END_IF\n"
            "3:\n"
            "    closeCmd := TRUE;\n"
            "    IF presence OR obstacle THEN\n"
            "        stage := 1;\n"
            "        hold(IN := FALSE, PT := T#3s);\n"
            "    ELSIF closeLimit THEN\n"
            "        stage := 0;\n"
            "    END_IF\n"
            "END_CASE\n"),
    }]},
)

# ---------------------------------------------------------------------------
# medium 1: conveyor sorting by height
# ---------------------------------------------------------------------------
_t(
    id="self_medium_001", source="self_built", difficulty="medium",
    title="传送带高度分拣", pou={"type": "function_block", "name": "HeightSort"},
    requirement={
        "zh": "传送带上按物品高度分拣到三箱：高度 <10 到 1 号箱，10..20 到 2 号箱，>20 到 3 号箱。"
              "分拣信号 risingSort 的上升沿触发一次分拣，输出对应箱号选择 binSel(1/2/3)。",
        "en": "Sort items into three bins by height: <10 to bin 1, 10..20 to bin 2, "
              ">20 to bin 3. A rising edge of risingSort triggers one sort; binSel "
              "outputs the chosen bin (1/2/3).",
    },
    interface={
        "duts": [], "inouts": [],
        "inputs": [
            {"name": "height", "type": "REAL", "desc": "物品高度"},
            {"name": "risingSort", "type": "BOOL", "desc": "分拣触发"},
        ],
        "outputs": [
            {"name": "binSel", "type": "INT", "desc": "选中的箱号 1/2/3"},
            {"name": "sortPulse", "type": "BOOL", "desc": "分拣脉冲"},
        ],
    },
    meta={"scenario": "离散分拣，边沿触发 + 区间判定，考查区间比较与边沿检测。"},
    ltl_specs=[
        {"id": "P1", "description": "箱号范围合法。",
         "formula": "G(binSel >= 1 && binSel <= 3)"},
    ],
    test_cases=[
        {"id": "TC1", "description": "区间分拣(每次分拣为上升沿)", "scan_ms": 10, "steps": [
            {"inputs": {"height": 5.0, "risingSort": True}, "expect": {"binSel": 1, "sortPulse": True}},
            {"inputs": {"height": 15.0, "risingSort": False}, "expect": {"sortPulse": False}},
            {"inputs": {"height": 15.0, "risingSort": True}, "expect": {"binSel": 2, "sortPulse": True}},
            {"inputs": {"height": 25.0, "risingSort": False}, "expect": {"sortPulse": False}},
            {"inputs": {"height": 25.0, "risingSort": True}, "expect": {"binSel": 3, "sortPulse": True}},
        ]},
    ],
    reference={"duts": [], "pous": [{
        "name": "HeightSort", "kind": "function_block",
        "declaration": (
            "FUNCTION_BLOCK HeightSort\n"
            "VAR_INPUT\n    height : REAL;\n    risingSort : BOOL;\nEND_VAR\n"
            "VAR_OUTPUT\n    binSel : INT;\n    sortPulse : BOOL;\nEND_VAR\n"
            "VAR\n    prev : BOOL;\n    edge : BOOL;\nEND_VAR\n"),
        "implementation": (
            "edge := risingSort AND NOT prev;\n"
            "prev := risingSort;\n"
            "sortPulse := edge;\n"
            "IF edge THEN\n"
            "    IF height < 10.0 THEN\n"
            "        binSel := 1;\n"
            "    ELSIF height <= 20.0 THEN\n"
            "        binSel := 2;\n"
            "    ELSE\n"
            "        binSel := 3;\n"
            "    END_IF\n"
            "END_IF\n"),
    }]},
)

# ---------------------------------------------------------------------------
# medium 2: duty-standby pump alternation
# ---------------------------------------------------------------------------
_t(
    id="self_medium_002", source="self_built", difficulty="medium",
    title="主备泵交替运行", pou={"type": "function_block", "name": "PumpAlternation"},
    requirement={
        "zh": "两台水泵一用一备：每次启动请求 start 上升沿时，轮流让 1 号或 2 号泵作为主泵运行；"
              "stop 时全部停止。若主泵运行反馈在启动后 2 秒内未到位，则切换备用泵。",
        "en": "Two pumps in duty/standby: each start rising edge alternates the lead pump "
              "(1 or 2). stop stops all. If the lead pump run feedback is absent within "
              "2s of start, switch to the standby pump.",
    },
    interface={
        "duts": [], "inouts": [],
        "inputs": [
            {"name": "start", "type": "BOOL", "desc": "启动请求"},
            {"name": "stop", "type": "BOOL", "desc": "停止"},
            {"name": "pump1Feedback", "type": "BOOL", "desc": "1 号泵运行反馈"},
            {"name": "pump2Feedback", "type": "BOOL", "desc": "2 号泵运行反馈"},
        ],
        "outputs": [
            {"name": "pump1Run", "type": "BOOL", "desc": "1 号泵运行"},
            {"name": "pump2Run", "type": "BOOL", "desc": "2 号泵运行"},
        ],
    },
    meta={"scenario": "流程行业主备切换，含运行反馈与定时切泵，考查边沿 + 定时 + 切换逻辑。"},
    ltl_specs=[
        {"id": "P1", "description": "停止时两泵均停。",
         "formula": "G(stop -> (!pump1Run && !pump2Run))"},
        {"id": "P2", "description": "至多一泵运行(主备)。",
         "formula": "G(!(pump1Run && pump2Run))"},
    ],
    test_cases=[
        {"id": "TC1", "description": "交替启动", "scan_ms": 10, "steps": [
            {"inputs": {"start": True, "stop": False, "pump1Feedback": True, "pump2Feedback": False},
             "expect": {"pump1Run": True, "pump2Run": False}},
            {"inputs": {"start": False, "stop": True, "pump1Feedback": False, "pump2Feedback": False},
             "expect": {"pump1Run": False, "pump2Run": False}},
            {"inputs": {"start": True, "stop": False, "pump1Feedback": False, "pump2Feedback": True},
             "expect": {"pump1Run": False, "pump2Run": True}},
        ]},
    ],
    reference={"duts": [], "pous": [{
        "name": "PumpAlternation", "kind": "function_block",
        "declaration": (
            "FUNCTION_BLOCK PumpAlternation\n"
            "VAR_INPUT\n    start : BOOL;\n    stop : BOOL;\n    pump1Feedback : BOOL;\n"
            "    pump2Feedback : BOOL;\nEND_VAR\n"
            "VAR_OUTPUT\n    pump1Run : BOOL;\n    pump2Run : BOOL;\nEND_VAR\n"
            "VAR\n    lead : INT := 1;\n    startPrev : BOOL;\n    startEdge : BOOL;\n"
            "    switchTof : TOF;\nEND_VAR\n"),
        "implementation": (
            "startEdge := start AND NOT startPrev;\n"
            "startPrev := start;\n"
            "IF stop THEN\n"
            "    pump1Run := FALSE;\n"
            "    pump2Run := FALSE;\n"
            "    lead := 1;\n"
            "ELSIF startEdge THEN\n"
            "    IF lead = 1 THEN\n"
            "        pump1Run := TRUE;\n"
            "        pump2Run := FALSE;\n"
            "    ELSE\n"
            "        pump1Run := FALSE;\n"
            "        pump2Run := TRUE;\n"
            "    END_IF\n"
            "    lead := 3 - lead;\n"
            "END_IF\n"
            "switchTof(IN := (pump1Run AND NOT pump1Feedback) OR (pump2Run AND NOT pump2Feedback),\n"
            "          PT := T#2s);\n"
            "IF switchTof.Q THEN\n"
            "    IF pump1Run THEN\n"
            "        pump1Run := FALSE;\n"
            "        pump2Run := TRUE;\n"
            "    ELSIF pump2Run THEN\n"
            "        pump2Run := FALSE;\n"
            "        pump1Run := TRUE;\n"
            "    END_IF\n"
            "END_IF\n"),
    }]},
)

# ---------------------------------------------------------------------------
# medium 3: alarm latch with acknowledge/reset
# ---------------------------------------------------------------------------
_t(
    id="self_medium_003", source="self_built", difficulty="medium",
    title="报警闭锁与确认复位", pou={"type": "function_block", "name": "AlarmLatch"},
    requirement={
        "zh": "报警输入 alarmIn 的上升沿触发闭锁报警 alarmLatched，并保持到复位 reset；"
              "acknowledge 为 TRUE 时静音 horn 但保留报警指示，直到 reset 清除。",
        "en": "A rising edge of alarmIn latches alarmLatched until reset. acknowledge "
              "silences horn but keeps the alarm indication until reset clears it.",
    },
    interface={
        "duts": [], "inouts": [],
        "inputs": [
            {"name": "alarmIn", "type": "BOOL", "desc": "报警输入"},
            {"name": "acknowledge", "type": "BOOL", "desc": "确认"},
            {"name": "reset", "type": "BOOL", "desc": "复位"},
        ],
        "outputs": [
            {"name": "alarmLatched", "type": "BOOL", "desc": "闭锁报警指示"},
            {"name": "horn", "type": "BOOL", "desc": "声光报警(确认后静音)"},
        ],
    },
    meta={"scenario": "报警管理，闭锁 + 确认 + 复位，考查边沿闭锁与优先级。"},
    ltl_specs=[
        {"id": "P1", "description": "确认后静音。",
         "formula": "G(acknowledge -> !horn)"},
        {"id": "P2", "description": "复位清除报警。",
         "formula": "G(reset -> !alarmLatched)"},
    ],
    test_cases=[
        {"id": "TC1", "description": "报警闭锁确认复位", "scan_ms": 10, "steps": [
            {"inputs": {"alarmIn": False, "acknowledge": False, "reset": False},
             "expect": {"alarmLatched": False, "horn": False}},
            {"inputs": {"alarmIn": True, "acknowledge": False, "reset": False},
             "expect": {"alarmLatched": True, "horn": True}},
            {"inputs": {"alarmIn": False, "acknowledge": True, "reset": False},
             "expect": {"alarmLatched": True, "horn": False}},
            {"inputs": {"alarmIn": False, "acknowledge": False, "reset": True},
             "expect": {"alarmLatched": False, "horn": False}},
        ]},
    ],
    reference={"duts": [], "pous": [{
        "name": "AlarmLatch", "kind": "function_block",
        "declaration": (
            "FUNCTION_BLOCK AlarmLatch\n"
            "VAR_INPUT\n    alarmIn : BOOL;\n    acknowledge : BOOL;\n    reset : BOOL;\nEND_VAR\n"
            "VAR_OUTPUT\n    alarmLatched : BOOL;\n    horn : BOOL;\nEND_VAR\n"
            "VAR\n    prev : BOOL;\n    edge : BOOL;\nEND_VAR\n"),
        "implementation": (
            "edge := alarmIn AND NOT prev;\n"
            "prev := alarmIn;\n"
            "IF reset THEN\n"
            "    alarmLatched := FALSE;\n"
            "ELSIF edge THEN\n"
            "    alarmLatched := TRUE;\n"
            "END_IF\n"
            "horn := alarmLatched AND NOT acknowledge;\n"),
    }]},
)

# ---------------------------------------------------------------------------
# medium 4: star-delta motor start
# ---------------------------------------------------------------------------
_t(
    id="self_medium_004", source="self_built", difficulty="medium",
    title="星三角降压启动", pou={"type": "function_block", "name": "StarDelta"},
    requirement={
        "zh": "电机星三角降压启动：start 上升沿先闭合主接触器与星形接触器，运行 5 秒后切换为"
              "主接触器与三角形接触器；stop 或热过载 overload 时立即断开所有接触器。",
        "en": "Star-delta start: a start rising edge closes main + star contactors for 5s, "
              "then switches to main + delta. stop or overload opens all contactors.",
    },
    interface={
        "duts": [], "inouts": [],
        "inputs": [
            {"name": "start", "type": "BOOL", "desc": "启动"},
            {"name": "stop", "type": "BOOL", "desc": "停止"},
            {"name": "overload", "type": "BOOL", "desc": "热过载"},
        ],
        "outputs": [
            {"name": "mainContactor", "type": "BOOL", "desc": "主接触器"},
            {"name": "starContactor", "type": "BOOL", "desc": "星形接触器"},
            {"name": "deltaContactor", "type": "BOOL", "desc": "三角形接触器"},
        ],
    },
    meta={"scenario": "电机启动控制，星三角切换 + 过载保护，考查定时切换与互锁。"},
    ltl_specs=[
        {"id": "P1", "description": "星形与三角形互锁。",
         "formula": "G(!(starContactor && deltaContactor))"},
        {"id": "P2", "description": "过载时全部断开。",
         "formula": "G(overload -> (!mainContactor && !starContactor && !deltaContactor))"},
    ],
    test_cases=[
        {"id": "TC1", "description": "星形运行 5s 后切三角形", "scan_ms": 1000, "steps": [
            {"inputs": {"start": True, "stop": False, "overload": False},
             "expect": {"mainContactor": True, "starContactor": True, "deltaContactor": False}},
            {"inputs": {"start": False, "stop": False, "overload": False},
             "repeat": 4, "expect": {"mainContactor": True, "starContactor": True, "deltaContactor": False}},
            {"inputs": {"start": False, "stop": False, "overload": False},
             "repeat": 1, "expect": {"mainContactor": True, "starContactor": False, "deltaContactor": True}},
        ]},
    ],
    reference={"duts": [], "pous": [{
        "name": "StarDelta", "kind": "function_block",
        "declaration": (
            "FUNCTION_BLOCK StarDelta\n"
            "VAR_INPUT\n    start : BOOL;\n    stop : BOOL;\n    overload : BOOL;\nEND_VAR\n"
            "VAR_OUTPUT\n    mainContactor : BOOL;\n    starContactor : BOOL;\n"
            "    deltaContactor : BOOL;\nEND_VAR\n"
            "VAR\n    stage : INT := 0;\n    startPrev : BOOL;\n    startEdge : BOOL;\n"
            "    starTon : TON;\nEND_VAR\n"),
        "implementation": (
            "startEdge := start AND NOT startPrev;\n"
            "startPrev := start;\n"
            "IF stop OR overload THEN\n"
            "    stage := 0;\n"
            "    mainContactor := FALSE;\n"
            "    starContactor := FALSE;\n"
            "    deltaContactor := FALSE;\n"
            "    starTon(IN := FALSE, PT := T#5s);\n"
            "ELSIF startEdge THEN\n"
            "    stage := 1;\n"
            "    mainContactor := TRUE;\n"
            "    starContactor := TRUE;\n"
            "    deltaContactor := FALSE;\n"
            "END_IF\n"
            "IF stage = 1 THEN\n"
            "    starTon(IN := TRUE, PT := T#5s);\n"
            "    IF starTon.Q THEN\n"
            "        stage := 2;\n"
            "        starContactor := FALSE;\n"
            "        deltaContactor := TRUE;\n"
            "    END_IF\n"
            "END_IF\n"),
    }]},
)

# ---------------------------------------------------------------------------
# hard 1: parking lot occupancy
# ---------------------------------------------------------------------------
_t(
    id="self_hard_001", source="self_built", difficulty="hard",
    title="停车场车位计数", pou={"type": "function_block", "name": "ParkingLot"},
    requirement={
        "zh": "停车场最多 capacity 个车位。entrySensor 上升沿计数加 1，exitSensor 上升沿计数减 1；"
              "count 达到 capacity 时 fullIndicator 为 TRUE 且禁止 entryGate 开闸。计数不得为负。",
        "en": "A parking lot holds up to capacity cars. entrySensor rising edge increments, "
              "exitSensor rising edge decrements. When count reaches capacity, fullIndicator "
              "is TRUE and entryGate is blocked. count must never be negative.",
    },
    interface={
        "duts": [], "inouts": [],
        "inputs": [
            {"name": "entrySensor", "type": "BOOL", "desc": "入口检测"},
            {"name": "exitSensor", "type": "BOOL", "desc": "出口检测"},
            {"name": "capacity", "type": "INT", "desc": "总车位"},
        ],
        "outputs": [
            {"name": "count", "type": "INT", "desc": "当前车辆数"},
            {"name": "fullIndicator", "type": "BOOL", "desc": "满位指示"},
            {"name": "entryGate", "type": "BOOL", "desc": "入口闸机"},
        ],
    },
    meta={"scenario": "离散计数与上限约束，考查双向计数、边界约束与互斥。"},
    ltl_specs=[
        {"id": "P1", "description": "计数不越界。",
         "formula": "G(count >= 0 && count <= capacity)"},
        {"id": "P2", "description": "满位时禁止入场。",
         "formula": "G(count >= capacity -> !entryGate)"},
    ],
    test_cases=[
        {"id": "TC1", "description": "进出计数与满位", "scan_ms": 10, "steps": [
            {"inputs": {"entrySensor": False, "exitSensor": False, "capacity": 3},
             "expect": {"count": 0, "fullIndicator": False, "entryGate": True}},
            {"inputs": {"entrySensor": True, "exitSensor": False, "capacity": 3},
             "expect": {"count": 1, "entryGate": True}},
            {"inputs": {"entrySensor": False, "exitSensor": False, "capacity": 3},
             "expect": {"count": 1}},
            {"inputs": {"entrySensor": True, "exitSensor": False, "capacity": 3},
             "expect": {"count": 2}},
            {"inputs": {"entrySensor": False, "exitSensor": False, "capacity": 3},
             "expect": {"count": 2}},
            {"inputs": {"entrySensor": True, "exitSensor": False, "capacity": 3},
             "expect": {"count": 3, "fullIndicator": True, "entryGate": False}},
            {"inputs": {"entrySensor": False, "exitSensor": True, "capacity": 3},
             "expect": {"count": 2, "fullIndicator": False, "entryGate": True}},
        ]},
    ],
    reference={"duts": [], "pous": [{
        "name": "ParkingLot", "kind": "function_block",
        "declaration": (
            "FUNCTION_BLOCK ParkingLot\n"
            "VAR_INPUT\n    entrySensor : BOOL;\n    exitSensor : BOOL;\n    capacity : INT;\nEND_VAR\n"
            "VAR_OUTPUT\n    count : INT;\n    fullIndicator : BOOL;\n    entryGate : BOOL;\nEND_VAR\n"
            "VAR\n    enPrev : BOOL;\n    exPrev : BOOL;\n    enEdge : BOOL;\n    exEdge : BOOL;\nEND_VAR\n"),
        "implementation": (
            "enEdge := entrySensor AND NOT enPrev;\n"
            "exEdge := exitSensor AND NOT exPrev;\n"
            "enPrev := entrySensor;\n"
            "exPrev := exitSensor;\n"
            "IF enEdge AND NOT exEdge THEN\n"
            "    IF count < capacity THEN\n"
            "        count := count + 1;\n"
            "    END_IF\n"
            "ELSIF exEdge AND NOT enEdge THEN\n"
            "    IF count > 0 THEN\n"
            "        count := count - 1;\n"
            "    END_IF\n"
            "END_IF\n"
            "fullIndicator := (count >= capacity);\n"
            "entryGate := NOT fullIndicator;\n"),
    }]},
)

# ---------------------------------------------------------------------------
# hard 2: constant-pressure water supply (multi-pump staging)
# ---------------------------------------------------------------------------
_t(
    id="self_hard_002", source="self_built", difficulty="hard",
    title="恒压供水多泵投切", pou={"type": "function_block", "name": "ConstPressure"},
    requirement={
        "zh": "恒压供水由 3 台泵组成。压力低于 setpoint-deadband 时逐台增加运行泵数，高于 "
              "setpoint+deadband 时逐台减少；运行泵数 0..3。",
        "en": "Constant-pressure supply with 3 pumps. Add pumps one by one when pressure "
              "is below setpoint-deadband; shed pumps when above setpoint+deadband; running "
              "pump count stays 0..3.",
    },
    interface={
        "duts": [], "inouts": [],
        "inputs": [
            {"name": "pressure", "type": "REAL", "desc": "管网压力"},
            {"name": "setpoint", "type": "REAL", "desc": "设定压力"},
            {"name": "deadband", "type": "REAL", "desc": "死区"},
        ],
        "outputs": [
            {"name": "pump1Run", "type": "BOOL", "desc": "1 号泵"},
            {"name": "pump2Run", "type": "BOOL", "desc": "2 号泵"},
            {"name": "pump3Run", "type": "BOOL", "desc": "3 号泵"},
        ],
    },
    meta={"scenario": "流程行业恒压控制，多泵分级投切 + 死区，考查分级逻辑与计数。"},
    ltl_specs=[
        {"id": "P1", "description": "压力过低时至少一台泵运行。",
         "formula": "G(pressure < setpoint - deadband -> (pump1Run || pump2Run || pump3Run))"},
        {"id": "P2", "description": "压力过高时全停。",
         "formula": "G(pressure > setpoint + deadband -> (!pump1Run && !pump2Run && !pump3Run))"},
    ],
    test_cases=[
        {"id": "TC1", "description": "分级投切", "scan_ms": 10, "steps": [
            {"inputs": {"pressure": 8.0, "setpoint": 10.0, "deadband": 1.0},
             "expect": {"pump1Run": True, "pump2Run": False, "pump3Run": False}},
            {"inputs": {"pressure": 8.0, "setpoint": 10.0, "deadband": 1.0},
             "expect": {"pump1Run": True, "pump2Run": True, "pump3Run": False}},
            {"inputs": {"pressure": 8.0, "setpoint": 10.0, "deadband": 1.0},
             "expect": {"pump1Run": True, "pump2Run": True, "pump3Run": True}},
        ]},
    ],
    reference={"duts": [], "pous": [{
        "name": "ConstPressure", "kind": "function_block",
        "declaration": (
            "FUNCTION_BLOCK ConstPressure\n"
            "VAR_INPUT\n    pressure : REAL;\n    setpoint : REAL;\n    deadband : REAL;\nEND_VAR\n"
            "VAR_OUTPUT\n    pump1Run : BOOL;\n    pump2Run : BOOL;\n    pump3Run : BOOL;\nEND_VAR\n"
            "VAR\n    n : INT := 0;\n    delayTon : TON;\nEND_VAR\n"),
        "implementation": (
            "IF pressure < setpoint - deadband AND n < 3 THEN\n"
            "    n := n + 1;\n"
            "ELSIF pressure > setpoint + deadband AND n > 0 THEN\n"
            "    n := n - 1;\n"
            "END_IF\n"
            "pump1Run := (n >= 1);\n"
            "pump2Run := (n >= 2);\n"
            "pump3Run := (n >= 3);\n"),
    }]},
)

# ---------------------------------------------------------------------------
# hard 3: simplified 3-floor elevator
# ---------------------------------------------------------------------------
_t(
    id="self_hard_003", source="self_built", difficulty="hard",
    title="三层电梯控制", pou={"type": "function_block", "name": "Elevator"},
    requirement={
        "zh": "简化三层电梯：目标楼层 targetFloor(1..3) 的上升沿触发；电梯运行到目标楼层"
              "(对应 floorSensor 为 TRUE) 后停止并开门 3 秒。上下方向由目标楼层与当前楼层比较决定。",
        "en": "Simplified 3-floor elevator: a rising edge of targetFloor(1..3) starts motion; "
              "the car stops when the target floor sensor is active, then opens the door 3s. "
              "Direction is up/down by comparing target and current floor.",
    },
    interface={
        "duts": [], "inouts": [],
        "inputs": [
            {"name": "targetFloor", "type": "INT", "desc": "目标楼层 1..3"},
            {"name": "floorSensor1", "type": "BOOL", "desc": "1 层到位"},
            {"name": "floorSensor2", "type": "BOOL", "desc": "2 层到位"},
            {"name": "floorSensor3", "type": "BOOL", "desc": "3 层到位"},
        ],
        "outputs": [
            {"name": "motorUp", "type": "BOOL", "desc": "上行"},
            {"name": "motorDown", "type": "BOOL", "desc": "下行"},
            {"name": "doorOpen", "type": "BOOL", "desc": "开门"},
        ],
    },
    meta={"scenario": "运动控制电梯，目标楼层 + 到位检测 + 开门延时，考查状态机与方向判定。"},
    ltl_specs=[
        {"id": "P1", "description": "上下行互斥。",
         "formula": "G(!(motorUp && motorDown))"},
        {"id": "P2", "description": "开门时电梯不运动。",
         "formula": "G(doorOpen -> (!motorUp && !motorDown))"},
    ],
    test_cases=[
        {"id": "TC1", "description": "上行到目标层并开门", "scan_ms": 1000, "steps": [
            {"inputs": {"targetFloor": 3, "floorSensor1": True, "floorSensor2": False, "floorSensor3": False},
             "expect": {"motorUp": True, "motorDown": False, "doorOpen": False}},
            {"inputs": {"targetFloor": 3, "floorSensor1": False, "floorSensor2": True, "floorSensor3": False},
             "expect": {"motorUp": True, "motorDown": False, "doorOpen": False}},
            {"inputs": {"targetFloor": 3, "floorSensor1": False, "floorSensor2": False, "floorSensor3": True},
             "expect": {"motorUp": False, "motorDown": False, "doorOpen": False}},
            {"inputs": {"targetFloor": 3, "floorSensor1": False, "floorSensor2": False, "floorSensor3": True},
             "expect": {"motorUp": False, "motorDown": False, "doorOpen": True}},
        ]},
    ],
    reference={"duts": [], "pous": [{
        "name": "Elevator", "kind": "function_block",
        "declaration": (
            "FUNCTION_BLOCK Elevator\n"
            "VAR_INPUT\n    targetFloor : INT;\n    floorSensor1 : BOOL;\n"
            "    floorSensor2 : BOOL;\n    floorSensor3 : BOOL;\nEND_VAR\n"
            "VAR_OUTPUT\n    motorUp : BOOL;\n    motorDown : BOOL;\n    doorOpen : BOOL;\nEND_VAR\n"
            "VAR\n    current : INT := 1;\n    stage : INT := 0;\n    doorTon : TON;\nEND_VAR\n"),
        "implementation": (
            "motorUp := FALSE;\n"
            "motorDown := FALSE;\n"
            "doorOpen := FALSE;\n"
            "CASE stage OF\n"
            "0:\n"
            "    IF floorSensor1 THEN current := 1;\n"
            "    ELSIF floorSensor2 THEN current := 2;\n"
            "    ELSIF floorSensor3 THEN current := 3;\n"
            "    END_IF\n"
            "    IF targetFloor > current THEN\n"
            "        motorUp := TRUE;\n"
            "    ELSIF targetFloor < current THEN\n"
            "        motorDown := TRUE;\n"
            "    ELSE\n"
            "        stage := 1;\n"
            "    END_IF\n"
            "1:\n"
            "    doorOpen := TRUE;\n"
            "    doorTon(IN := TRUE, PT := T#3s);\n"
            "    IF doorTon.Q THEN\n"
            "        stage := 0;\n"
            "    END_IF\n"
            "END_CASE\n"),
    }]},
)


def dump():
    os.makedirs(OUT, exist_ok=True)
    for t in TASKS:
        tc_annotations.apply(t)  # 每步测试目的 / 初始状态 / 覆盖内容 / 规约关联
        fn = os.path.join(OUT, t["id"] + ".json")
        with open(fn, "w", encoding="utf-8") as f:
            json.dump(t, f, ensure_ascii=False, indent=2)
        print("wrote", fn)


if __name__ == "__main__":
    dump()
