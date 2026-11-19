# rna_ss_f1_mcc

## 干什么用的

用 RNet2 预测的二级结构和参考规范配对算 F1 / MCC。

## 什么时候用它

RNA 设计里 motif 二级结构保真度的量化。

## 基本信息

- **一句话**：Motif-restricted secondary-structure F1 and MCC of an RNet2 prediction against the reference's canonical pairs
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("rna_ss_f1_mcc", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--rna_ss_f1_mcc.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("rna_ss_f1_mcc", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `predictions_csv` | `str` | **必填** | RNet2 runner 输出的 CSV。必须含 'predicted_dbn' 列和 'join_on' 指定的键列。 |
| `join_on` | `str` | `"design_path"` | 与 handler 共用、用于把预测匹配到设计的列。不用行位置——runner 会保序，但 Chaperone 的块不一定。 |
| `reference_pairs` | `List[List[str]]` | _运行时计算_ | 作为参考残基 id 的规范配对（WC + G.U），如 [["A5", "A10"], ["A12", "A25"]]。通过 diffused_index_map 解析。仅含规范配对——其余见 pseudoknot 字段。 |
| `pseudoknot_pairs` | `List[List[str]]` | _运行时计算_ | 因属于假结而从 R 中排除的参考配对。 |
| `compare_to_vienna` | `bool` | `true` | 同时报告同一设计上 RNet 与 ViennaRNA MFE 的全序列 F1。跨方法二维结构不一致是廉价的警示信号。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
