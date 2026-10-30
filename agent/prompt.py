"""Prompt construction for the ST generation agent."""
from __future__ import annotations

FORMAT_SPEC = """\
严格按以下块格式输出代码（不要输出其它内容，不要用 markdown 代码围栏）：

<<<DUT name=类型名 kind=struct>>>
TYPE 类型名 :
STRUCT
    字段 : 类型;
END_STRUCT
END_TYPE
<<<END>>>

<<<POU name=功能块名 kind=function_block>>>
FUNCTION_BLOCK 功能块名
VAR_INPUT
    输入 : 类型;
END_VAR
VAR_OUTPUT
    输出 : 类型;
END_VAR
VAR
    内部变量 : 类型;
END_VAR
<<<IMPL>>>
实现语句体（不要重复 FUNCTION_BLOCK 头）
<<<END>>>

- 只需要输出的 POU（题目要求的那个），以及题目接口中声明的 DUT（如有）。
- 一次输出必须包含完整代码；修改时同样输出完整代码，不要只给补丁。
- 若题目要求 PROGRAM，kind 写 program，声明头用 PROGRAM。
"""

SYSTEM_PROMPT = """\
你是精通 CODESYS V3.5 SP22 的 IEC 61131-3 结构化文本（ST）工程师。
根据题目需求生成可直接编译通过的 CODESYS ST 代码。

输出格式要求：
%s
硬性编译规则（CODESYS 特有，务必遵守）：
1. 接口必须与题目完全一致：输入/输出/输入输出参数的名称与类型必须一字不差。
2. 标识符不能以下划线开头；避免使用保留字（如 BIT、SUB、AT、REF）作为变量名。
3. 字符串下标从 0 开始：s[i] 取第 i+1 个字符。
4. TON/TOF 首次调用 ET=0，PT 等于 K 个扫描周期时在第 K+1 次调用置 Q。
5. FOR 循环递减用 "TO ... BY -1"，不支持 DOWNTO。
6. 不支持 VARIANT、__VARCINFO；只使用 Standard 库（TON/TOF/R_TRIG/F_TRIG/CTU 等）。
7. 布尔用 TRUE/FALSE；时间用 T#5s、LTIME 用 LTIME#500h；整型常量可写 16#8001。
8. 不要使用外部库、条件编译或未声明的全局变量。
9. 变量默认值写在声明中（如 counter : INT := 0;）。
10. 实现必须语义完整：初始状态、保持、优先级、边界条件都要覆盖。
11. 输出保持精简：不写大段注释、不复述需求、不重复代码；必须确保一次输出在长度限制内
    完整结束（每个块都以 <<<END>>> 结尾）。

LTL 规约是行为要求的精确表述，生成代码必须满足全部规约。
""" % FORMAT_SPEC


def _fmt_interface(task):
    itf = task["interface"]
    lines = []
    groups = (("inputs", "输入"), ("outputs", "输出"), ("inouts", "输入输出"))
    for key, label in groups:
        items = itf.get(key, [])
        if not items:
            continue
        lines.append("### %s" % label)
        lines.append("| 名称 | 类型 | 说明 |")
        lines.append("| --- | --- | --- |")
        for e in items:
            lines.append("| `%s` | `%s` | %s |"
                         % (e["name"], e["type"], e.get("desc", "")))
        lines.append("")
    for d in itf.get("duts", []):
        lines.append("### 数据类型 %s（%s）" % (d["name"], d.get("kind", "struct")))
        if d.get("fields"):
            lines.append("| 字段 | 类型 | 说明 |")
            lines.append("| --- | --- | --- |")
            for f in d["fields"]:
                lines.append("| `%s` | `%s` | %s |"
                             % (f["name"], f["type"], f.get("desc", "")))
        lines.append("")
    return "\n".join(lines)


def task_prompt(task):
    req = task["requirement"]
    parts = [
        "# 任务：%s" % task["title"],
        "",
        "## 需求（中文）",
        req.get("zh") or req.get("en", ""),
    ]
    if req.get("zh") and req.get("en"):
        parts += ["", "## 需求（English）", req["en"]]
    parts += [
        "",
        "## 接口定义",
        _fmt_interface(task),
        "## 形式化规约（LTL，必须满足）",
    ]
    for s in task.get("ltl_specs", []):
        parts.append("- %s：%s\n  `%s`"
                     % (s["id"], s.get("description", ""), s["formula"]))
    parts += [
        "",
        "## 输出要求",
        "POU 名称必须为 `%s`（%s）。" % (task["pou"]["name"], task["pou"]["type"]),
        "只输出题目要求的 POU 和接口声明的 DUT，按块格式输出完整代码。",
    ]
    return "\n".join(parts)


def compile_feedback(attempt, errors, max_items=20):
    lines = ["第 %d 次生成后编译失败，共 %d 个错误（已去重）："
             % (attempt, len(errors))]
    for e in errors[:max_items]:
        loc = e.get("position_text") or ""
        code = e.get("code") or ""
        lines.append("- %s %s: %s" % (code, loc, e.get("text", "")))
    if len(errors) > max_items:
        lines.append("- ...（其余 %d 条省略）" % (len(errors) - max_items))
    lines += [
        "",
        "请修正上述问题并重新输出**全部**文件块（完整代码，不要补丁）。",
    ]
    return "\n".join(lines)


def interface_feedback(errors):
    return ("问题（接口不匹配，未进入编译）：\n"
            + "\n".join("- " + e for e in errors)
            + "\n\n请按题目接口定义修正后重新输出全部文件块。")


def test_feedback(attempt, failures):
    lines = ["第 %d 次生成的代码编译通过，但行为测试未通过：" % attempt]
    for f in failures[:10]:
        lines.append("- %s 第 %d 步：%s"
                     % (f.get("testCase"), f.get("step"), f.get("desc", "")))
        for k, exp, act in f.get("mismatches", []):
            lines.append("    输出 %s 应为 %s，实际为 %s" % (k, exp, act))
    lines += ["", "请修正逻辑并重新输出**全部**文件块。"]
    return "\n".join(lines)
