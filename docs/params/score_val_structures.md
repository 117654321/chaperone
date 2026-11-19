# score_val_structures

## 干什么用的

用验证参考给预测结构打分。

## 什么时候用它

结构预测验证流程的打分环节。

## 基本信息

- **一句话**：Score predictions against manifested validation references
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("score_val_structures", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--score_val_structures.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("score_val_structures", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `metrics` | `list[blocks.networks.prediction.validation.score.ValidationM` | _运行时计算_ | 要运行的后端：rf3_allatom_lddt 和/或 peppr。 |
| `remap_outputs_to_input` | `bool` | `false` | 打分前把重新编号的单体预测映射到被评分的那个蛋白 pn 单元。默认关闭，以便参考与输出的直接比较不受约束。 |
| `min_atom_coverage` | `float` | `0.95` | 重映射的 oracle 输出必须覆盖的已解析参考原子最小比例。仅在开启 remap_outputs_to_input 时使用。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
