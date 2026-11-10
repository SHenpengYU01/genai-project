# 面向 CODESYS 平台的 ST 代码自动生成系统

自研 Coding Agent + 实验框架：生成 IEC 61131-3 结构化文本（ST）→ CODESYS 编译 →
CODESYS 仿真行为测试 → 结构化修复，并在 30 道 PLC 编程题上做多模型对比评测。

## 仓库结构

| 目录 | 内容 |
|------|------|
| `codesys/` | CODESYS 平台接入（见 `codesys/README.md`），分两层：`compile/` 编译检查（CPython 客户端 + IronPython worker + 模板工程，DUT/Standard 库支持）；`simulate/` 行为测试（ST 自测驱动生成 + CODESYS 仿真执行） |
| `dataset/` | 30 道题（20 公共 + 10 自建），含 LTL 规约、测试用例（含逐步测试目的/覆盖内容/关联规约）、可编译参考实现；schema、校验与用例文档渲染脚本 |
| `agent/` | 自研 ST 生成 Agent harness（LLM 客户端、提示、解析、编译/测试反馈循环） |
| `baseline/` | 现有框架基线：Codex CLI（经 DMXAPI responses 协议驱动，同一评测管线） |
| `experiments/` | 实验编排与指标汇总；`mocks/` 为离线自测用的脚本化模型输出 |
| `report/` | 实验报告（环境、数据集与 LTL、框架设计、四设置结果与分析）+ 测试用例文档 |
| `presentation/` | 5 分钟汇报 slides（ZJU Beamer 模板，`concise/main.tex` 源码 + `main.pdf`）+ 讲稿与时间分配 |
| `公共题库.json` / `任务说明.md` | 原始题目与作业要求 |

## 环境

- Windows + CODESYS V3.5 SP22 Patch 4（x64），`CODESYS.exe` 在 PATH（Control Win V3 x64 模板）
- Python 3.8+（仅标准库）

## 快速开始

```bash
# 0) 配置模型密钥：复制模板并填写 DMXAPI_API_KEY（.env 已被 .gitignore 忽略）
copy .env.example .env
python -m agent.llm          # 检查密钥/模型名是否就绪（只显示掩码）
python -m agent.llm --list qwen   # 有 key 后列出可用模型 id

# 1) 编译服务自检（7 个样例，含故意报错项）
codesys\compile\run_examples.bat

# 2) 数据集质量门槛：参考实现必须编译通过
python dataset/check_references.py

# 3) 数据集自检：参考实现必须通过自己的测试用例（CODESYS 仿真）
python codesys/simulate/selfcheck.py

# 4) Agent 离线自测（无需 API key，回放 mock 输出）
python experiments/build_mocks.py
python experiments/run_eval.py --mock reference --limit 3 --outdir experiments/runs/mock_ref

# 5) 正式实验（DMXAPI：填好 .env 的 DMXAPI_API_KEY）
python experiments/run_eval.py --models deepseek,qwen \
    --model-names deepseek=deepseek-v4.1-flash,qwen=qwen3.7-flash \
    --outdir experiments/runs/agent_2models

# 6) 基线框架（Codex CLI，同提示/同轮次/同管线）
python experiments/run_eval.py --framework codex --models deepseek,qwen \
    --max-rounds 5 --resume --outdir experiments/runs/codex_2models

# 7) 生成测试用例文档（跑参考实现逐拍实测实际输出，约 10-20 分钟）
python dataset/render_cases.py

# 8) 汇总任一运行目录为 Markdown 表
python experiments/summarize.py experiments/runs/agent_2models
```

## 交付物索引

| 作业要求 | 位置 |
|---|---|
| 数据集（公共 20 + 自建 10）与 schema | `dataset/tasks/`、`dataset/schema.md`、`dataset/build_*.py` |
| 来源/改编/合理性/多样性说明 | 报告 §2.2–2.4；自建题 `meta.scenario` |
| 逐题 LTL 规约（75 条） | `dataset/tasks/*.json` 的 `ltl_specs`；报告附录 A |
| 逐题测试用例（54 组 / 199 步，含每步测试目的） | `report/测试用例.md`（按作业模板渲染）；数据 `dataset/tasks/*.json` 的 `test_cases`；说明文字 `dataset/tc_annotations.py`；执行器 `codesys/simulate/` |
| 自研 Agent harness | `agent/`（见 `agent/README.md`） |
| CODESYS 编译集成 | `codesys/compile/`（见 `codesys/compile/README.md`） |
| 自动行为测试（加分项） | `codesys/simulate/`（CODESYS 仿真 + 自测驱动，见 `codesys/README.md`） |
| 现有框架基线 | `baseline/`（Codex CLI，见其 README） |
| 四设置实验结果 | `experiments/RESULTS_FULL.md`、`experiments/results.csv`（含 Codex+Qwen 解析器修复后的重跑说明） |
| 实验报告 | `report/实验报告.md` |
| 汇报 slides（5 分钟） | `presentation/concise/main.pdf`、`presentation/concise/讲稿.md` |

## 实验报告

- [实验报告（含逐题 LTL 规约与四设置结果分析）](report/实验报告.md)
- [测试用例文档（按作业模板：名称/初始状态/输入与步骤/预期输出/覆盖内容/实际输出/检查内容）](report/测试用例.md)
- [四设置结果汇总表](experiments/RESULTS_FULL.md)
- [汇报 slides（5 分钟，含讲稿）](presentation/concise/main.pdf)

## 实验指标

- 编译通过率：首次（第 1 轮）与修改 n 次后的通过率
- 测试通过率：按行为测试用例（CODESYS 仿真）统计
- 资源消耗：token 用量、估算费用、墙钟时间、平均修复轮次
- 工具/基础设施故障（`tool_error`）单列，不计入模型能力

## 已知环境约束（实测）

- 脚本化创建的工程需手动引用 Standard 库（TON/R_TRIG 等），编译服务已自动处理
- 标识符不能以下划线开头；`BIT`、`SUB` 为保留字
- 字符串下标 0 基；`FOR` 递减用 `TO ... BY -1`（无 `DOWNTO`）
- 不支持 `VARIANT` / `__VARCINFO`（FIFO 题已相应改编为 `INT` 元素 + `ARRAY[*]`）
