# -*- coding: utf-8 -*-
"""Generate report/Appendix_EN.md from report/附录.md (tables only).

The appendix is pure tabular data plus section titles, so the English version is
produced mechanically: IDs, POU names, LTL formulas and ✓/✗ marks stay as-is, while
task titles, source labels, setting labels, statuses and blockers are mapped.
"""
import io
import re

TITLES = {
    "public_easy_001": "Automated filling line control",
    "public_easy_002": "Double-word edge detection",
    "public_easy_003": "Alarm handling with hysteresis",
    "public_easy_004": "Jam pump debouncing and run maintenance",
    "public_easy_005": "Weld-gap alarm and start inhibition",
    "public_easy_006": "Aeration blower delayed start",
    "public_medium_001": "Multi-pump rotating water supply",
    "public_medium_002": "Moving average computation",
    "public_medium_003": "Temperature control logic",
    "public_medium_004": "Analog batch conversion",
    "public_medium_005": "Automated production line control",
    "public_medium_006": "Slab thickness alarm and fault history",
    "public_medium_007": "Office HVAC multi-mode energy-saving control",
    "public_medium_008": "IPv4 address parsing",
    "public_hard_001": "Recipe management system",
    "public_hard_002": "Material batching process control",
    "public_hard_003": "Five-station production control",
    "public_hard_004": "Flexible machining control",
    "public_hard_005": "Robotic arm control",
    "public_hard_006": "FIFO first-in-first-out queue",
    "self_easy_001": "Two-phase traffic light",
    "self_easy_002": "Tank level control with high-high alarm",
    "self_easy_003": "Automatic door control",
    "self_medium_001": "Conveyor height sorting",
    "self_medium_002": "Duty/standby pump alternation",
    "self_medium_003": "Alarm latching with acknowledge and reset",
    "self_medium_004": "Star-delta reduced-voltage start",
    "self_hard_001": "Parking lot occupancy counting",
    "self_hard_002": "Constant-pressure multi-pump staging",
    "self_hard_003": "Three-floor elevator control",
}
SETTING = {
    "自研+DeepSeek": "Self-built+DeepSeek",
    "自研+Qwen": "Self-built+Qwen",
    "Codex+DeepSeek": "Codex+DeepSeek",
    "Codex+Qwen": "Codex+Qwen",
}
SRC = {"公共": "Public", "自建": "Self-built"}
BLOCKER = {"测试未通过": "Tests failed", "编译未通过": "Compile failed"}
COLUMN_HEADER = {"编号", "设置", "任务"}

HEADERS = {
    "A": ["## Appendix A: Per-task formal specifications", "",
          "| ID | Task | Difficulty | Source | POU | LTL specifications |",
          "| --- | --- | --- | --- | --- | --- |"],
    "B": ["## Appendix B: Tasks that did not succeed", "",
          "| Setting | Task | Difficulty | Termination status | Rounds "
          "| Blocker |",
          "| --- | --- | --- | --- | --- | --- |"],
    "C": ["## Appendix C: Per-task four-setting results (all tests passed?)", "",
          "| Task | Difficulty | Title | Self-built+DeepSeek | Self-built+Qwen "
          "| Codex+DeepSeek | Codex+Qwen |",
          "| --- | --- | --- | --- | --- | --- | --- |"],
}


def cells(line):
    return [x.strip() for x in re.split(r"\s\|\s", line.strip().strip("|"))]


def convert(section, c):
    """Return the English row for one Chinese table row."""
    if section == "A":
        tid, _title, diff, src, pou, ltl = c
        return "| %s | %s | %s | %s | %s | %s |" % (
            tid, TITLES[tid], diff, SRC[src], pou, ltl)
    if section == "B":
        setting, tid, diff, status, rounds, blocker = c
        return "| %s | %s | %s | %s | %s | %s |" % (
            SETTING[setting], tid, diff, status, rounds, BLOCKER[blocker])
    tid, diff, _title, a, b, cc, d = c
    return "| %s | %s | %s | %s | %s | %s | %s |" % (
        tid, diff, TITLES[tid], a, b, cc, d)


def main():
    lines = io.open("report/附录.md", encoding="utf-8").read().splitlines()
    out = []
    for line in lines:
        st = line.strip()
        if st.startswith("## 附录"):
            section = st.split()[2]
            if out:
                out.append("")
            out.extend(HEADERS[section])
            continue
        if not st or st.startswith("| ---") or st.startswith("|---"):
            continue        # source blank lines / separators: we emit our own
        if st.startswith("|"):
            c = cells(st)
            if c[0] in COLUMN_HEADER:
                continue
            out.append(convert(section, c))
            continue
        out.append(st)
    text = "\n".join(out).lstrip("\n") + "\n"
    io.open("report/Appendix_EN.md", "w", encoding="utf-8",
            newline="\n").write(text)
    print("wrote report/Appendix_EN.md (%d lines)" % len(out))


if __name__ == "__main__":
    main()
