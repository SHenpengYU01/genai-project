# 题目数据 Schema

每道题一个 JSON 文件，放在 `dataset/tasks/` 下。文件名的 `source_difficulty_序号` 便于排序，`id` 是稳定标识。

## 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | 是 | 稳定标识，如 `public_easy_001`、`self_medium_003` |
| `source` | string | 是 | `public`（公共题）或 `self_built`（自建题） |
| `difficulty` | string | 是 | `easy` / `medium` / `hard` |
| `title` | string | 是 | 题目标题 |
| `pou` | object | 是 | `{ "type": "function_block"\|"program"\|"function", "name": "..." }` |
| `requirement` | object | 是 | `{ "zh": "...", "en": "..." }`，自然语言需求全文；`en` 对自建题可省略 |
| `interface` | object | 是 | 见下 |
| `ltl_specs` | array | 是 | 见下 |
| `test_cases` | array | 是 | 见下 |
| `reference` | object | 是 | 参考实现，用于验证仿真器与测试用例本身正确 |
| `meta` | object | 否 | 自建题的来源/改编/合理性说明（写入报告用） |

## `interface`

```json
{
  "duts":   [ { "name": "ST_Pump", "kind": "struct",
                "fields": [ { "name": "priority", "type": "INT", "desc": "" } ] } ],
  "inputs":  [ { "name": "StartBtn", "type": "BOOL", "desc": "" } ],
  "outputs": [ { "name": "Motor", "type": "BOOL", "desc": "" } ],
  "inouts":  [ { "name": "pumpGroup", "type": "ARRAY[1..5] OF ST_Pump", "desc": "" } ]
}
```

- `type` 是 CODESYS 类型字符串（含 `ARRAY[...] OF ...`、`STRING(n)` 等）。
- `inouts[].capacity`（可选）：`ARRAY[*]` 变长数组的具体容量提示，测试驱动据此分配存储
  （不给时按测试向量中出现的最大长度推断）。
- `duts[].kind`：`struct` / `enum` / `alias` / `union`；`struct` 用 `fields` 描述成员，
  `enum` 用 `values` 描述取值列表。

## `ltl_specs`

```json
{ "id": "P1", "description": "停止安全性：…", "formula": "G((StopBtn || EStop) -> X(!Motor))" }
```

- `formula` 用 ASCII 记法：`G`(always) `F`(eventually) `X`(next) `U`(until)，
  逻辑用 `!` `&&` `||` `->`。接入 PLCVerif 时再翻译成其输入语法。
- 每道题至少覆盖「安全性」与「活性/功能正确」两类性质，逐条可追溯。

## `test_cases`

```json
{ "id": "TC1", "description": "正常启动与保持", "scan_ms": 10,
  "initialState": "新建功能块实例，内部状态与输出全部清零；输入取下表周期 0 的取值。",
  "coverage": ["初始化后保持停止", "满足条件时启动（P2）", "松开启动按钮后自保持运行"],
  "specRefs": ["P2"],
  "steps": [
    { "purpose": "初始化：无启动信号，电机停止",
      "inputs": { "StartBtn": false, "StopBtn": false, "EStop": false },
      "expect": { "Motor": false } }
  ] }
```

- 执行语义：对每个 test_case，初始化 FB 内部状态；按 `steps` 顺序，每步
  「设 inputs → 跑一个扫描周期 → 读取并比较 `expect` 中的输出」。`expect` 是
  **该周期结束后**的输出值。
- **只比较 `expect` 中列出的输出（及其元素/成员）**，未列出的输出不做检查。
  若某步确实要求"其余输出为 FALSE"，需在 `expect` 中显式写 `false`；
  空 `expect` 表示该步只推进状态、不做任何断言。
- `step.repeat`（可选，默认 1）：该步的 inputs 连续保持 N 个扫描周期，`expect`
  在第 N 个周期结束后**断言一次**（用于让定时器/状态机推进，避免手写几十步）。
- 涉及定时器的题，`scan_ms` 表示每个 step 代表的扫描周期时长，仿真器据此累加时间。
- 状态型题目（含边沿/保持）的测试用例要覆盖：初始态、触发、保持、复位、优先级冲突。

### 模板要求的人工说明字段（`dataset/tc_annotations.py` 维护）

作业文档「测试用例模板与示例」要求每个用例写清名称、初始状态、输入、预期输出、
覆盖内容与实际结果。其中机器不可推导的部分以独立字段存放，`validate.py` 强制非空：

| 字段 | 级别 | 含义 |
|------|------|------|
| `test_cases[].initialState` | 用例 | 开始测试前的实例状态（冷启动清零、定时器未启动、外部缓冲初值等） |
| `test_cases[].coverage` | 用例 | 该用例检查的功能点、状态变化、边界与异常情况（字符串数组） |
| `test_cases[].specRefs` | 用例 | 该用例提供证据的 LTL 规约 id（必须是 `ltl_specs` 中存在的 id） |
| `steps[].purpose` | 步 | 该扫描周期的检查目的（模板表格中的「检查内容」列） |

这些字段由 `dataset/tc_annotations.py` 在构建时注入（两个 build 脚本都会调用
`apply()`），**不要手工改 `dataset/tasks/*.json`**：改注解后重跑
`python dataset/build_public.py && python dataset/build_self.py`。
`python dataset/render_cases.py` 会把它们连同参考实现的实测输出渲染成
`report/测试用例.md`。

## `reference`

与编译服务 `compile_jobs` 的作业结构一致：

```json
{ "duts": [ { "name": "ST_Pump", "kind": "struct", "declaration": "TYPE ... END_TYPE" } ],
  "pous": [ { "name": "MotorCtrl", "kind": "function_block",
              "declaration": "FUNCTION_BLOCK ...", "implementation": "..." } ] }
```

- 含 `VAR_IN_OUT` 的题，`reference` 需自带调用它的 PROGRAM（并对应 `auto_wire:false`），
  否则编译服务无法判定其函数体。
- 用途：跑仿真器/测试用例前，先用 reference 编译通过 + 测试通过，证明「题可做、
  测试用例正确、仿真器正确」；再拿模型生成的代码跑同一套测试，指标才可信。
