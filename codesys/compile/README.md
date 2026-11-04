# CODESYS ST 编译检查（`codesys/compile`）

无状态、批处理的 ST 代码编译/诊断服务。Agent 框架只需提供 **ST 代码文本**，
服务负责：准备 CODESYS 工程 → 注入 POU → 编译 → 结构化提取报错 → 返回 JSON。
调用方完全不需要了解 CODESYS 工程结构。

- 目标版本：CODESYS V3.5 SP22 Patch 4（x64），本机 `D:\_ALLAPPS\CODESYS`
- 运行宿主：CODESYS 内置 IronPython 2.7（服务内部）；客户端为任意 CPython 3
- 目录可整体拷贝到其他装有同版本 CODESYS 的机器（路径均相对脚本定位）
- 同层兄弟目录 `../simulate/` 是行为测试（仿真执行）；模板工程 `../template.project`
  由两者共用。两者的分工见 `../README.md`。

## 1. 文件清单

| 文件 | 作用 |
|------|------|
| `worker.py` | IronPython 批编译 worker（在 CODESYS 进程内运行） |
| `run_compile.bat` | 启动器：`CODESYS.exe --noUI --runscript worker.py ...` |
| `client.py` | **CPython 3 客户端（推荐调用入口）**，纯标准库 |
| `../template.project` | 干净模板工程（Control Win V3 x64 + Application + MainTask + 空 PLC_PRG），自检 0 错误 |
| `../make_template.py` / `../run_make_template.bat` | 模板工程再生成脚本（模板损坏时使用） |
| `examples/` | 请求样例、批处理样例、Agent 修复循环示例、DUT 回归测试 |
| `work/` | 临时工程与请求文件，可随时清空（已 gitignore） |

## 2. 接口契约

### 请求 JSON（UTF-8）

单作业对象，或 `{"jobs": [作业, ...]}` 数组（推荐，**一次冷启动编译多个作业**）：

```json
{
  "id": "case001",
  "auto_wire": true,
  "keep_project": false,
  "pous": [
    {
      "name": "MotorCtrl",
      "kind": "function_block",
      "declaration": "FUNCTION_BLOCK MotorCtrl\nVAR_INPUT\n  StartBtn : BOOL;\nEND_VAR\nVAR_OUTPUT\n  Motor : BOOL;\nEND_VAR\n",
      "implementation": "Motor := StartBtn;\n"
    }
  ]
}
```

字段：

- `id`（可选）：作业标识，原样回传。
- `pous[].name`：**必填**。
- `pous[].kind`：`program` / `function_block` / `function`。省略时：
  名字为 `PLC_PRG` 视为 program，其余视为 function_block。
- `pous[].declaration` / `implementation`：声明区与实现区**完整文本**（含
  `FUNCTION_BLOCK ...`/`PROGRAM ...` 头）。换行用 `\n`。
- `duts`（可选）：`[{ "name", "kind", "declaration" }]`，声明结构体/枚举/别名/
  联合等自定义类型。`kind` 默认 `struct`（取值 `struct`/`enum`/`alias`/`union`，
  内部映射到 CODESYS 的 `Structure`/`Enumeration`/`Alias`/`Union`）；
  `declaration` 为完整 `TYPE ... END_TYPE` 文本。DUT 在 POU 之前创建，供 POU 引用。
- FUNCTION 的返回类型：从声明头 `FUNCTION f : INT` 自动解析；也可用
  `return_type` 显式指定。
- `auto_wire`（默认 true）：见第 4 节，**必须理解**。
- `keep_project`：true 时保留填充后的工程副本（响应里给路径），便于人工排查。

### 响应 JSON（UTF-8）

```json
{
  "ok": true,
  "elapsed_ms": 25399,
  "error": null,
  "results": [
    {
      "id": "case001",
      "passed": false,
      "fatal": null,
      "elapsed_ms": 5765,
      "errors": [
        { "severity": "Error", "category": "编译",
          "text": "没有定义标识符'undeclared_var' ",
          "code": "C46", "position_text": "行2,列1 (Impl)",
          "position": "18", "length": "14" }
      ],
      "warnings": [],
      "info_count": 5,
      "wire_warnings": [],
      "project_copy": null
    }
  ]
}
```

- `passed`：该作业**编译错误数为 0**。
- `errors[]/warnings[]`：`code`（编译器错误码，如 C46/C18）、
  `position_text`（中文行列信息）、`position`/`length`（字符偏移与跨度，
  可用于精确回标到模型生成的代码）、`text`（中文消息原文）。
- `fatal`：工具/注入阶段异常（如 POU 名非法、FUNCTION 返回类型解析失败、
  工程打不开）。**fatal 表示"无法判定代码"，不等于代码有错**，应重试或排查。
- `wire_warnings`：自动接线限制提示（见第 4 节）。
- 顶层 `ok=false` 时整个 worker 崩溃，错误堆栈在 `error`。

## 3. 三种调用方式

### (a) CPython 库（推荐）

```python
from client import compile_st, compile_jobs        # codesys/compile/client.py

# 单个 POU
r = compile_st(name="MotorCtrl", kind="function_block",
               declaration=DECL, implementation=IMPL)
if r["passed"]:
    ...
else:
    for e in r["errors"]:
        prompt += "%s %s: %s" % (e["code"], e["position_text"], e["text"])

# 批量（一次 CODESYS 冷启动跑完整个题库的一轮）
report = compile_jobs([job1, job2, job3])
```

### (b) 命令行（退出码即门禁）

```bat
python codesys/compile/client.py codesys/compile/examples/batch_all.json out.json
REM 0=全部通过  1=存在编译失败  2=工具/环境错误
```

### (c) 不经 CPython（其他语言宿主）

直接 `cmd /c run_compile.bat <req.json> <resp.json>`，再自行解析响应 JSON。

## 4. 关键语义：自动接线（auto_wire）

**CODESYS 的 rebuild() 只编译"从任务可达的调用图"。** 一个没被任何程序调用
的 FUNCTION_BLOCK / FUNCTION / PROGRAM，即使实现里写了未声明变量，编译也
报 0 错误（实测确认，极易造成假阳性）。

服务默认生成隐藏程序 `CI_HARNESS_PRG`（挂到 MainTask）：实例化作业内每个 FB、
用默认参数调用每个 FUNCTION，并把额外的 PROGRAM 直接挂到 MainTask，从而保证
**作业内所有 POU 都真正被编译**。`CI_HARNESS_PRG` 为保留名，不可作为 POU 名
（CODESYS 标识符不能以下划线开头，故不用 `__CI_PRG` 这类名字）。

已知限制（会出现在 `wire_warnings`，且该函数体**不被编译检查**）：

- 含 `VAR_IN_OUT` 的 FUNCTION；
- 输入参数为数组、结构体、枚举或无法安全构造默认值的类型；
- 含 `VAR_IN_OUT` 的 FUNCTION_BLOCK（`ci_fb_N();` 无法绑定 IN_OUT 形参，会
  被 auto_wire 跳过，函数体不被编译检查）。

对这类函数/功能块，调用方可在作业里自行提供一个调用它的 PROGRAM（此时设
`auto_wire: false` 或并存），确保其进入调用图。纯 BOOL/数值/TIME/STRING
输入的函数用 FALSE/0/T#0s/'' 等默认值调用。

**带结构体/数组的题目（如 `ST_Pump`、`ST_AnalogChannel`、`ST_Recipe`）提交范式：**
作业里同时给出 `duts`（类型定义）+ POU（FB/PROGRAM），并视 FB 是否含
`VAR_IN_OUT` 决定是否用 caller PROGRAM + `auto_wire: false`。见
`examples/test_dut.py`。

## 4.1 编码行为（实测）

- 请求 JSON 为 UTF-8，中文注释在 ST 代码中**完全允许**；
- 中文字符串**字面量**（如 `msg := '急停'`）会产生一条**警告**（非错误）：
  "字符串字面量…包含不可表示的字符"，提示启用工程选项"字符串使用UTF-8编码"。
  若数据集含中文字符串，请以 errors 判定通过性、忽略该类警告，或改用英文/ASCII 字符串。
- CODESYS 标识符（POU 名、变量名）不能以下划线开头，`CI_HARNESS_PRG`、
  `ci_fb_N`、`ci_r_N` 为接线程序保留名。

## 4.2 Standard 库（TON/R_TRIG 等）

脚本化创建的空工程默认**不引用 Standard 库**，会导致模型生成的
`TON/TOF/TP/R_TRIG/F_TRIG/CTU` 等标准功能块报"未知类型"。`worker.py`
已在每次编译前通过 `add_placeholder` 自动引用
`Standard, 3.5.22.0 (3S - Smart Software Solutions GmbH)`，因此定时器/触发器
功能块可正常编译。`bit` 是 CODESYS 保留类型名（`BIT`），不能用作变量名。

## 5. 性能与使用建议（CODESYS 冷启动是主要成本）

> 实测数据见下表（本机 SP22 P4，批内含若干 FB/FUNCTION/PROGRAM 作业）。

| 场景 | 实测耗时（2026-10-28，SP22 P4） |
|------|---------|
| 单次调用（1 个 POU，含 CODESYS 冷启动） | 约 6s |
| 批处理首作业 | 约 6s |
| 批内后续单作业 | 约 2.7–3.3s/个 |
| 7 作业整批 | 23.5s（平均 3.4s/作业） |

建议：

1. **批量化**：一轮修复把所有待编译作业放进一次 `compile_jobs`，不要每题
   起一次进程。
2. 修复循环终止条件：`passed==true` 或达到最大轮次；fatal 单独计为工具失败，
   不应算入模型的编译失败指标。
3. 公平性：基线框架与自研框架必须使用**同一模板工程、同一 worker 版本**，
   编译通过率才可比；记录每轮的 `elapsed_ms` 与客户端墙钟。

## 6. 故障处理约定

- worker 对每个作业隔离异常：单题注入/编译崩溃只影响该题（其 `fatal` 非空），
  不中断整批。
- 调用方需带进程级超时（客户端默认 300s/批）；超时后强制
  `taskkill /F /IM CODESYS.exe`，防止单实例僵尸转发后续调用。
- 若全部结果异常：先检查 CODESYS 是否能交互登录、Scripting 组件是否安装、
  `compile_console.log`（GBK 编码）中的原始输出。

## 7. 与作业指标的对应

- 首次编译通过率：第 1 轮 `passed==true` 的题数 / 总题数。
- 修改 n 次后通过率：第 n 轮（每次调用均返回结构化错误用于修复）。
- 工具错误（fatal）单列，不计入模型能力指标，保证结果可信。
- 测试通过率（行为级）属于下一阶段的测试向量执行器，本服务只保证"编译通过
  + 诊断可信"。
