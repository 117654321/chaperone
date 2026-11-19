# rna_thermo

## 干什么用的

用 ViennaRNA 算 Boltzmann 概率、配对概率、集合缺陷。

## 什么时候用它

评估 RNA motif 的热力学稳定性——配对是不是真的稳定。

## 基本信息

- **一句话**：ViennaRNA Boltzmann probability, pair probabilities and ensemble defect for a required motif pair set
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("rna_thermo", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--rna_thermo.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("rna_thermo", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `required_pairs` | `List[List[str]]` | _运行时计算_ | motif 需要的碱基配对，用参考残基 id 表示并经 diffused_index_map 解析，如 [["A10", "A24"], ["B4", "B5"]]。纯整数字符串按扩散下标处理。 |
| `pseudoknot_pairs` | `List[List[str]]` | _运行时计算_ | 构成假结的配对。因 ViennaRNA 模型无法表示而排除出约束；仍会报告并标记。 |
| `chain` | `Optional[str]` | `None` | 限定到某一个链 id。None 使用所有 RNA 残基。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
