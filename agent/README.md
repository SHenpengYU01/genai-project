# 自研 ST 生成 Agent（Phase 4）

轻量化 Agent harness：**生成 → 接口校验 → CODESYS 编译 → 行为测试 → 结构化反馈修复**，带上下文压缩与早停。

## 目录

| 文件 | 作用 |
|------|------|
| `llm.py` | OpenAI 兼容客户端（DeepSeek/Qwen，可用环境变量覆盖），含 token/成本统计；`MockClient` 用于离线自测 |
| `prompt.py` | 系统提示（CODESYS 编译规则 + 输出块格式）、题目提示（需求/接口/LTL）、编译/接口/测试反馈模板 |
| `parser.py` | 解析模型输出的 `<<<POU/DUT>>>` 块；接口一致性的**编译前**静态校验 |
| `caller_gen.py` | 生成 `PLC_PRG` 调用者程序，保证含 `VAR_IN_OUT` 的 FB 真正进入编译图 |
| `harness.py` | 主循环、终止条件、实验记录 |

## 主循环

```
任务(需求+接口+LTL) ──► LLM 生成完整块 ──► 解析/接口校验
        ▲                                    │ 失败：结构化反馈（不花编译成本）
        │                                    ▼
        └── 编译错误/测试失败反馈 ◄── CODESYS 编译 ◄─ 通过 ─► 行为测试(仿真)
                                     │ 通过                       │ 失败
                                     └──────────► 成功 ◄──────────┘
```

- **编译**：`tool/codesys_build.compile_jobs`，单作业；`auto_wire:false` + 自动生成的 `PLC_PRG` 调用者，
  对 `VAR_IN_OUT`/结构体/数组参数同样做真实编译检查。
- **测试**：`tester/run.py`，在 CODESYS 仿真（Control Win V3）里逐拍执行测试用例；
  失败时回传「用例/步骤/期望值/实际值（首失败步快照）」。
- **上下文管理**：错误按 `(code, text)` 去重并计数；历史只保留最近 2 轮对话（system+题目常驻），
  避免重复输入膨胀。
- **终止条件**：① 成功；② 达到 `max_rounds`（默认 5）；③ 代码与上一轮完全相同（stalled）；
  ④ 失败签名连续 2 次相同（no_progress）；⑤ 基础设施错误（tool_error，单列不计入模型指标）。

## 使用

```bash
# 配置密钥：复制模板并填写（.env 不入库，.env.example 入库）
cp .env.example .env        # Windows: copy .env.example .env
python -m agent.llm         # 检查密钥/模型名是否就绪（掩码显示）
python -m agent.llm --list qwen   # 有 key 后列出可用模型 id，避免模型名写错

# 离线自测（回放 mock 输出）
python -m agent.harness --task dataset/tasks/public_easy_003.json --mock

# 真实模型（走 DMXAPI）
python -m agent.harness --task dataset/tasks/public_easy_003.json --model deepseek
python -m agent.harness --task ... --model qwen --model-name qwen3-max
```

密钥优先级：进程环境变量 > `.env`（仓库根目录，可用 `AGENT_ENV_FILE` 指定其他路径）。
`.env` 已在 `.gitignore` 中；`.env.example` 为提交的模板。

模型配置（端点：DMXAPI `https://www.dmxapi.cn/v1`，OpenAI 兼容）：

| alias | 默认模型名（可覆盖） | 覆盖变量 | 密钥环境变量 |
|---|---|---|---|
| `deepseek` | `deepseek-v4.1-flash` | `DMXAPI_MODEL_DEEPSEEK` | `DMXAPI_API_KEY` |
| `qwen` | `qwen3.7-flash` | `DMXAPI_MODEL_QWEN` | `DMXAPI_API_KEY` |

- 准确模型名以 [DMXAPI 模型与价格页](https://www.dmxapi.cn/rmb) 为准；填到 `.env`
  或命令行 `--model-name`（`run_eval.py --model-names deepseek=...,qwen=...`）。
- 通用覆盖：`AGENT_BASE_URL` / `AGENT_MODEL` / `AGENT_API_KEY`（`AGENT_MODEL` 同时作用于所有 alias，一般只用于单模型调试）。
- 成本估算默认关闭（DMXAPI 按人民币计价，价格以页面为准）；需要时在 `agent/llm.py`
  的 `DEFAULT_MODELS` 中填写 `price_in` / `price_out`（每百万 token）。

## 实验

```bash
# 生成 mock（reference / broken_once / test_fail_once）
python experiments/build_mocks.py

# 离线端到端验证（推荐在改动 harness 后先跑）
python experiments/run_eval.py --mock reference   --outdir experiments/runs/mock_ref
python experiments/run_eval.py --mock broken_once --tasks public_easy_003 --outdir experiments/runs/x

# 正式实验：模型 A/B × 30 题
python experiments/run_eval.py --models deepseek,qwen --outdir experiments/runs/agent_2models
python experiments/run_eval.py --models deepseek --no-tests --outdir experiments/runs/compile_only
```

产物：`<outdir>/tasks/<model>__<task>.json`（逐题完整记录：每轮代码/编译/测试/用量/耗时）
与 `<outdir>/summary.json`（总体 + 分难度指标）。

## 指标口径

- **首次编译通过率**：第 1 轮 `compile.passed`。
- **最终编译通过率**：最后一次编译 `passed`。
- **测试通过率**：`tests.allPass`（行为测试全通过）；也可用逐用例 `passCnt/(passCnt+failCnt)`。
- **成本/时间**：token 用量、估算费用、墙钟时间、平均轮次。
- `tool_error`（CODESYS/仿真基础设施故障）不计入模型能力，单列统计。

## 设计取舍与局限

- **测试用例对模型不可见**（prompt 只给需求/接口/LTL），避免指标虚高；
  基线框架使用同一份提示内容与同样的轮次/超时上限，保证可比。
- 接口在编译前做静态校验（名称/类型必须与题目一致），失败反馈不消耗 CODESYS 冷启动。
- 提示中内置 CODESYS 特有问题（`BIT`/`SUB` 保留字、字符串 0 基索引、TON 首拍 ET=0、
  `FOR ... BY -1`、不支持 VARIANT），这些是**编译环境事实**而非解题提示。
- 行为测试基于 CODESYS 官方仿真运行时（非自研解释器），语义与编译器一致；
  PLCVerif 形式化验证暂未接入（规约已写入数据集，可作为后续扩展）。
