# 四设置对比实验结果（自研 harness vs Codex CLI × DeepSeek/Qwen）

- 日期：2026-11-02
- 网关：DMXAPI (`https://www.dmxapi.cn/v1`)
- 模型：DeepSeek `deepseek-v4.1-flash-1017`、Qwen `qwen3.7-flash`
- 数据集：30 题（20 公共 + 10 自建；easy 9 / medium 12 / hard 9）
- 设置：两框架同提示、同反馈文本、同 max_rounds=5、同编译/测试管线
- 代码版本：b4c000f

数据来源：experiments/runs/agent_2models, experiments/runs/codex_2models

## 总体指标

| 框架 | 模型 | 任务数 | 首次编译 | 最终编译 | 测试通过 | 端到端成功 | 平均轮次 | 平均耗时(s) | 输入tokens | 输出tokens |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 自研 harness | deepseek-v4.1-flash-1017 | 30 | 96.7% | 100.0% | 83.3% | 83.3% | 1.77 | 163 | 75058 | 383312 |
| 自研 harness | qwen3.7-flash | 30 | 76.7% | 93.3% | 66.7% | 66.7% | 2.53 | 295 | 131255 | 503606 |
| Codex CLI | deepseek-v4.1-flash-1017 | 30 | 100.0% | 100.0% | 83.3% | 83.3% | 1.70 | 342 | 565110 | 521147 |
| Codex CLI | qwen3.7-flash | 30 | 16.7% | 53.3% | 33.3% | 33.3% | 4.00 | 431 | 1632869 | 358524 |

## 实验设置矩阵（首次编译通过率 / 测试通过率）

| 框架 | deepseek-v4.1-flash-1017 | qwen3.7-flash |
| --- | --- | --- |
| 自研 harness | 96.7% / 83.3% | 76.7% / 66.7% |
| Codex CLI | 100.0% / 83.3% | 16.7% / 33.3% |

## 分难度（测试通过率）

| 框架 | 模型 | easy | medium | hard |
| --- | --- | --- | --- | --- |
| 自研 harness | deepseek-v4.1-flash-1017 | 77.8% | 91.7% | 77.8% |
| 自研 harness | qwen3.7-flash | 55.6% | 83.3% | 55.6% |
| Codex CLI | deepseek-v4.1-flash-1017 | 88.9% | 83.3% | 77.8% |
| Codex CLI | qwen3.7-flash | 55.6% | 16.7% | 33.3% |

## 未成功任务

| 框架 | 模型 | 任务 | 难度 | 状态 | 轮次 | 卡点 |
| --- | --- | --- | --- | --- | --- | --- |
| 自研 harness | deepseek-v4.1-flash-1017 | public_easy_005 | easy | max_rounds | 5 | 测试未通过 |
| 自研 harness | deepseek-v4.1-flash-1017 | public_hard_003 | hard | no_progress | 3 | 测试未通过 |
| 自研 harness | deepseek-v4.1-flash-1017 | public_hard_004 | hard | no_progress | 3 | 测试未通过 |
| 自研 harness | deepseek-v4.1-flash-1017 | public_medium_005 | medium | stalled | 4 | 测试未通过 |
| 自研 harness | deepseek-v4.1-flash-1017 | self_easy_003 | easy | no_progress | 3 | 测试未通过 |
| 自研 harness | qwen3.7-flash | public_easy_004 | easy | max_rounds | 5 | 测试未通过 |
| 自研 harness | qwen3.7-flash | public_easy_005 | easy | no_progress | 3 | 测试未通过 |
| 自研 harness | qwen3.7-flash | public_hard_003 | hard | no_progress | 3 | 测试未通过 |
| 自研 harness | qwen3.7-flash | public_hard_004 | hard | no_progress | 5 | 测试未通过 |
| 自研 harness | qwen3.7-flash | public_hard_006 | hard | max_rounds | 5 | 编译未通过 |
| 自研 harness | qwen3.7-flash | public_medium_003 | medium | no_progress | 3 | 测试未通过 |
| 自研 harness | qwen3.7-flash | public_medium_004 | medium | max_rounds | 5 | 编译未通过 |
| 自研 harness | qwen3.7-flash | self_easy_001 | easy | max_rounds | 5 | 测试未通过 |
| 自研 harness | qwen3.7-flash | self_easy_003 | easy | no_progress | 3 | 测试未通过 |
| 自研 harness | qwen3.7-flash | self_hard_003 | hard | max_rounds | 5 | 测试未通过 |
| Codex CLI | deepseek-v4.1-flash-1017 | public_hard_003 | hard | no_progress | 3 | 测试未通过 |
| Codex CLI | deepseek-v4.1-flash-1017 | public_hard_004 | hard | no_progress | 3 | 测试未通过 |
| Codex CLI | deepseek-v4.1-flash-1017 | public_medium_003 | medium | max_rounds | 5 | 测试未通过 |
| Codex CLI | deepseek-v4.1-flash-1017 | public_medium_005 | medium | no_progress | 3 | 测试未通过 |
| Codex CLI | deepseek-v4.1-flash-1017 | self_easy_003 | easy | no_progress | 3 | 测试未通过 |
| Codex CLI | qwen3.7-flash | public_easy_004 | easy | no_progress | 5 | 编译未通过 |
| Codex CLI | qwen3.7-flash | public_easy_005 | easy | no_progress | 4 | 测试未通过 |
| Codex CLI | qwen3.7-flash | public_hard_001 | hard | max_rounds | 5 | 编译未通过 |
| Codex CLI | qwen3.7-flash | public_hard_002 | hard | max_rounds | 5 | 测试未通过 |
| Codex CLI | qwen3.7-flash | public_hard_003 | hard | max_rounds | 5 | 编译未通过 |
| Codex CLI | qwen3.7-flash | public_hard_004 | hard | max_rounds | 5 | 编译未通过 |
| Codex CLI | qwen3.7-flash | public_hard_006 | hard | max_rounds | 5 | 编译未通过 |
| Codex CLI | qwen3.7-flash | public_medium_001 | medium | max_rounds | 5 | 测试未通过 |
| Codex CLI | qwen3.7-flash | public_medium_002 | medium | max_rounds | 5 | 编译未通过 |
| Codex CLI | qwen3.7-flash | public_medium_003 | medium | max_rounds | 5 | 编译未通过 |
| Codex CLI | qwen3.7-flash | public_medium_004 | medium | max_rounds | 5 | 测试未通过 |
| Codex CLI | qwen3.7-flash | public_medium_005 | medium | max_rounds | 5 | 编译未通过 |
| Codex CLI | qwen3.7-flash | public_medium_006 | medium | max_rounds | 5 | 编译未通过 |
| Codex CLI | qwen3.7-flash | public_medium_007 | medium | max_rounds | 5 | 编译未通过 |
| Codex CLI | qwen3.7-flash | public_medium_008 | medium | max_rounds | 5 | 编译未通过 |
| Codex CLI | qwen3.7-flash | self_easy_001 | easy | max_rounds | 5 | 编译未通过 |
| Codex CLI | qwen3.7-flash | self_easy_003 | easy | max_rounds | 5 | 编译未通过 |
| Codex CLI | qwen3.7-flash | self_hard_003 | hard | max_rounds | 5 | 编译未通过 |
| Codex CLI | qwen3.7-flash | self_medium_002 | medium | no_progress | 5 | 测试未通过 |
| Codex CLI | qwen3.7-flash | self_medium_004 | medium | no_progress | 3 | 测试未通过 |
