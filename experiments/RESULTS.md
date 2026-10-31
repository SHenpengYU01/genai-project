# 自研 Agent 实验最终结果

- 日期：2026-10-31
- 网关：DMXAPI (`https://www.dmxapi.cn/v1`)
- 模型：DeepSeek `deepseek-v4.1-flash-1017`、Qwen `qwen3.7-flash`
- 数据集：30 题（20 公共 + 10 自建；easy 9 / medium 12 / hard 9）
- 设置：自研 harness，max_rounds=5，行为测试开启（CODESYS 仿真）
- 代码版本：6d47d77

实验配置：模型 ['deepseek', 'qwen']，任务 30 道，max_rounds=5，use_tests=True

## 总体指标

| 模型 | 任务数 | 首次编译通过率 | 最终编译通过率 | 测试通过率 | 端到端成功率 | 平均轮次 | 平均耗时(s) | 输入tokens | 输出tokens |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek (deepseek-v4.1-flash-1017) | 30 | 96.7% | 100.0% | 83.3% | 83.3% | 1.77 | 163 | 75058 | 383312 |
| qwen (qwen3.7-flash) | 30 | 76.7% | 93.3% | 66.7% | 66.7% | 2.53 | 295 | 131255 | 503606 |

## 分难度

| 模型 | 难度 | n | 首次编译 | 最终编译 | 测试通过 | 成功率 | 平均轮次 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek | easy | 9 | 100.0% | 100.0% | 77.8% | 77.8% | 2.11 |
| deepseek | medium | 12 | 91.7% | 100.0% | 91.7% | 91.7% | 1.67 |
| deepseek | hard | 9 | 100.0% | 100.0% | 77.8% | 77.8% | 1.56 |
| qwen | easy | 9 | 77.8% | 100.0% | 55.6% | 55.6% | 2.44 |
| qwen | medium | 12 | 75.0% | 91.7% | 83.3% | 83.3% | 2.33 |
| qwen | hard | 9 | 77.8% | 88.9% | 55.6% | 55.6% | 2.89 |

## 未成功任务

| 模型 | 任务 | 难度 | 状态 | 轮次 | 卡点 |
| --- | --- | --- | --- | --- | --- |
| deepseek | public_easy_005 | easy | max_rounds | 5 | 测试未通过 |
| deepseek | public_hard_003 | hard | no_progress | 3 | 测试未通过 |
| deepseek | public_hard_004 | hard | no_progress | 3 | 测试未通过 |
| deepseek | public_medium_005 | medium | stalled | 4 | 测试未通过 |
| deepseek | self_easy_003 | easy | no_progress | 3 | 测试未通过 |
| qwen | public_easy_004 | easy | max_rounds | 5 | 测试未通过 |
| qwen | public_easy_005 | easy | no_progress | 3 | 测试未通过 |
| qwen | public_hard_003 | hard | no_progress | 3 | 测试未通过 |
| qwen | public_hard_004 | hard | no_progress | 5 | 测试未通过 |
| qwen | public_hard_006 | hard | max_rounds | 5 | 编译未通过 |
| qwen | public_medium_003 | medium | no_progress | 3 | 测试未通过 |
| qwen | public_medium_004 | medium | max_rounds | 5 | 编译未通过 |
| qwen | self_easy_001 | easy | max_rounds | 5 | 测试未通过 |
| qwen | self_easy_003 | easy | no_progress | 3 | 测试未通过 |
| qwen | self_hard_003 | hard | max_rounds | 5 | 测试未通过 |
