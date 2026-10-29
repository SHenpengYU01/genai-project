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
  "steps": [
    { "inputs": { "StartBtn": false, "StopBtn": false, "EStop": false },
      "expect": { "Motor": false } }
  ] }
```

- 执行语义：对每个 test_case，初始化 FB 内部状态；按 `steps` 顺序，每步
  「设 inputs → 跑一个扫描周期 → 读 outputs 与 `expect` 比较」。`expect` 是
  **该周期结束后**的输出值；`expect` 中**未列出的输出隐式为 FALSE**。
- `step.repeat`（可选，默认 1）：该步的 inputs 连续保持 N 个扫描周期，`expect`
  在第 N 个周期结束后**断言一次**（用于让定时器/状态机推进，避免手写几十步）。
- 涉及定时器的题，`scan_ms` 表示每个 step 代表的扫描周期时长，仿真器据此累加时间。
- 状态型题目（含边沿/保持）的测试用例要覆盖：初始态、触发、保持、复位、优先级冲突。

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
