# examples/batch_all.json 预期结果（用于交付验收）

| id | 内容 | 预期 passed | 预期 errors | 备注 |
|----|------|------------|-------------|------|
| 01_fb_good | 电机启停 FB（无任务引用，靠 auto_wire） | true | 0 | 验证自动接线能让独立 FB 被编译 |
| 02_fb_bad_standalone | FB 内含 undeclared_var | **false** | 2（C46 未定义标识符、C18 无效赋值目标） | 接线后错误必须被抓到 |
| 03_program_good | PLC_PRG 计数器 | true | 0 | 模板任务已引用 PLC_PRG |
| 04_unicode_good | 中文注释 + 中文字符串字面量 | true | 0 | 验证 UTF-8 请求链路 |
| 05_function_bad | FUNCTION ClampIt:INT 内含 bad_identifier | **false** | 验证 FUNCTION return_type 解析 + 默认实参调用接线 |
| 06_function_inout_unwired | VAR_IN_OUT 函数且体内有坏变量 | true（假阴性已知） | 0 | 必须在 wire_warnings 中给出"未接线、未编译检查"提示 |
| 07_multi_pou_good | FUNCTION+FB+PLC_PRG 互调 | true | 0 | 多 POU 共存与用户自带调用图 |

任一 `fatal` 非空均为工具缺陷（与模型生成质量无关）。
