# CODESYS 平台接入（`codesys/`）

本目录是项目与 CODESYS 交互的**唯一入口**，分两层：

```
codesys/
├── template.project       干净模板工程（两层共用）
├── make_template.py       模板工程再生成脚本
├── run_make_template.bat
├── compile/               ① 编译检查：只要"编不编得过"
│   ├── client.py          CPython 客户端（compile_jobs / compile_st）
│   ├── worker.py          IronPython worker（在 CODESYS 进程内跑）
│   ├── run_compile.bat
│   ├── run_examples.bat
│   ├── examples/          请求样例 + DUT/VAR_IN_OUT 回归测试
│   └── work/              临时工程（gitignore）
└── simulate/              ② 行为测试：要"跑起来对不对"
    ├── driver.py          ST 自测驱动生成（把 test_cases 编成 PLC 内的断言程序）
    ├── runner.py          CPython 侧编排（_run_sim / run_task）
    ├── worker.py          IronPython worker（建工程 → 编译 → 登录仿真 → 读回结果）
    ├── run_simulation.bat
    ├── selfcheck.py       数据集自检：参考实现跑自己的用例
    ├── probe.py           单题调试：跑一题并读任意符号
    └── work/              临时工程（gitignore）
```

## 为什么分两层

| | `compile/` | `simulate/` |
|---|---|---|
| 输入 | 只有 ST 代码 | 代码 + 测试向量 |
| 输出 | 结构化诊断（`code` / `position_text` / `text`），`passed` | 每个用例、每个扫描步的通过情况 + 实测值 |
| 是否需要 PLC 运行时 | 否，只开 IDE 编译 | 是：`set_simulation_mode` → `login` → `start` → 跑完再读回 |
| 单次成本（实测） | ≈13 s（CODESYS 冷启动为主） | ≈24 s |
| 典型调用方 | Agent 修复循环的第一道门；`dataset/check_references.py` | Agent 修复循环的第二道门；`dataset/render_cases.py`；评测 |

Agent 的循环是「编译过了才付仿真的钱」：约一半的修复轮次在第 1 道门就被拦下，
同时把「模型写错代码」与「工具/仿真环境故障」分开统计（报告里的 `tool_error` 单列）。

两者共用同一套设施：同一个 `template.project`、同一种「`CODESYS.exe --noUI
--runscript=<worker> --scriptargs:'req.json resp.json'` + JSON 请求/响应」的调用方式、
各自独立的 `work/` 临时目录。

## 一致性约束

- `simulate/worker.py` 与 `compile/worker.py` **各自**建工程（复用模板、建 DUT/POU、
  注入 Standard 库），因为仿真必须在同一个 CODESYS 会话里完成"建工程 → 编译 →
  登录 → 跑"，跨进程会多付一次冷启动（≈13 s）。两边的建工程逻辑目前是重复的，
  改其中一处时**必须同步另一处**，并用 `codesys/verify_manifest.py`
  对比前后的编译/仿真结果（见下）。
- `compile/client.py` 与 `simulate/runner.py` 都用 `os.path.dirname(__file__)` 定位
  资源，因此**整个 `codesys/` 目录可以整体搬到另一台装了同版本 CODESYS 的机器**。
- 模板工程 `template.project` 在 `codesys/` 根，两个 worker 都用
  `os.path.join(dirname(HERE), "template.project")` 定位；移动模板时两处都要改。

## 一致性验证（重构/改动后必做）

`verify_manifest.py` 把服务的全部可观测产物打成清单，改动前后各生成一次再 diff。
它能自动识别新旧目录布局（`codesys/{compile,simulate}` 与重构前的 `tool/`+`tester/`），
因此基线可以在旧提交的工作树上采。

```bash
# 记录基线（drivers / compile / dut / references 四段，约 1 分钟）
python codesys/verify_manifest.py make --label before --skip-simulate

# 改动后再次记录并对比
python codesys/verify_manifest.py make --label after --skip-simulate
python codesys/verify_manifest.py diff before after
```

覆盖内容：

| 段 | 断言的理由 |
|---|---|
| `drivers` | 31 个任务生成的驱动文本 sha1（默认与 `trace=True` 两种），保证测试向量执行语义不变 |
| `compile` | `compile/examples/batch_all.json` 7 个作业的 `passed`、错误码/文本、wire 警告 |
| `dut` | `compile/examples/test_dut.py` 5 个作业的期望值（DUT / VAR_IN_OUT / enum 回归） |
| `references` | `dataset/check_references.py` 31 个文件的编译结论 |
| `simulate` | 每个任务的 `allPass/passCnt/failCnt` 与逐拍实测值 sha1（加 `--sim-from-cache` 复用 `dataset/.cache/`，或省略该段） |

本次重构（`tool/` + `tester/` → `codesys/`）的对照表，便于对照旧提交：

| 旧路径 | 新路径 |
|---|---|
| `tool/codesys_build.py` | `codesys/compile/client.py` |
| `tool/compile_worker.py` | `codesys/compile/worker.py` |
| `tool/run_compile.bat` | `codesys/compile/run_compile.bat` |
| `tool/run_tests.bat` | `codesys/compile/run_examples.bat` |
| `tool/examples/` | `codesys/compile/examples/` |
| `tool/README.md` | `codesys/compile/README.md` |
| `tool/template.project` | `codesys/template.project` |
| `tool/make_template.py` / `run_maketemplate.bat` | `codesys/make_template.py` / `codesys/run_make_template.bat` |
| `tester/driver_gen.py` | `codesys/simulate/driver.py` |
| `tester/run.py` | `codesys/simulate/runner.py` |
| `tester/simulate_worker.py` | `codesys/simulate/worker.py` |
| `tester/run_all.py` | `codesys/simulate/selfcheck.py` |
| `tester/debug_task.py` | `codesys/simulate/probe.py` |
| `tool/work/`、`tester/work/` | `codesys/compile/work/`、`codesys/simulate/work/` |

重构后的验证结果（同一提交的旧工作树 vs 新工作树）：`drivers`、`compile`、`dut`、
`references`、`simulate` 五段清单**完全一致**（0 处差异）。

## 常用命令

```bash
# 编译检查：7 个样例（含故意报错项），退出码即门禁
codesys\compile\run_examples.bat

# 编译服务回归：DUT / VAR_IN_OUT / enum
python codesys/compile/examples/test_dut.py

# 数据集自检：参考实现必须通过自己的测试用例（30 题，约 15 分钟）
python codesys/simulate/selfcheck.py
python codesys/simulate/selfcheck.py public_easy   # 只跑一批

# 单题调试：跑一题并读任意符号（例如 IP 解析的中间值）
python codesys/simulate/probe.py public_medium_008.json CI_TEST_DRIVER.fb[0].ipValue
```

## 从 Python 调用

```python
import sys
sys.path.insert(0, "codesys/compile")
sys.path.insert(0, "codesys/simulate")

from client import compile_jobs            # 编译检查
import driver, runner                     # 行为测试

report = compile_jobs([job1, job2])        # 一次 CODESYS 冷启动编译多个作业
res = runner.run_task(task, pous, duts)    # 跑完一组测试用例
```

`agent/harness.py`、`dataset/check_references.py`、`dataset/render_cases.py`
都按这种方式接入。
