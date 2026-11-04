# 基线框架：Codex CLI（Phase 5）

现有 Agent 框架基线。`baseline/codex_client.py` 把 `codex exec` 包装成与自研
harness 相同的客户端接口（`chat(messages)`），因此**提示内容、反馈轮次上限、
编译与行为测试管线完全复用**，两种框架的差异只在于"由谁组织生成过程"。

## 环境（实测）

- `codex-cli 0.164.0`
- Codex 0.164 已移除 `wire_api = "chat"`，必须使用 `responses`；
  DMXAPI 网关支持 `POST https://www.dmxapi.cn/v1/responses`（实测可用）
- 密钥复用 `.env` 的 `DMXAPI_API_KEY`；通过 `-c model_providers.dmxapi.env_key` 传递
- 每次调用：`--ephemeral --skip-git-repo-check --ignore-user-config
  -s read-only -C <临时目录>`，只取 `--output-last-message` 作为模型输出；
  token 用量从 `--json` 事件的 `turn.completed.usage` 统计

## 公平性约定

| 项 | 自研 harness | Codex 基线 |
|---|---|---|
| 题目提示 | 同一份（需求/接口/LTL） | 同一份（拼接为单条 prompt） |
| 修复反馈 | 编译错误/测试失败，最多 5 轮 | 同一反馈文本，最多 5 轮 |
| 编译 | `codesys/compile` 同一模板/worker | 同左 |
| 行为测试 | `codesys/simulate` CODESYS 仿真 | 同左 |
| 生成方式 | 单次 LLM 调用 | Codex 自身 agent 循环（工具、规划等） |

> Codex 在 read-only 沙箱中运行，无法修改工作区文件；提示要求"只输出代码块"，
> 其内部可能出现额外工具调用，这属于框架自身开销，计入 token/耗时。

## 运行

```bash
# 单题
python -m agent.harness --task dataset/tasks/public_easy_003.json \
    --framework codex --model deepseek --max-rounds 5

# 全量 30 题 × 2 模型（可断点续跑）
python experiments/run_eval.py --framework codex --models deepseek,qwen \
    --max-rounds 5 --resume --outdir experiments/runs/codex_2models

# 汇总
python experiments/summarize.py experiments/runs/codex_2models
```

## 已知问题

- `codex.cmd` 需用完整路径（Windows PATH 下 `codex` 是无扩展名的 shim，
  Python `subprocess` 直接调用会 `FileNotFoundError`；客户端已用
  `shutil.which("codex.cmd")` 解析）
- stdin 必须 UTF-8 字节流（Windows 默认 GBK 会触发 `input is not valid UTF-8`）
