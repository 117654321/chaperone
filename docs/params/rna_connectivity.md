# rna_connectivity

## 干什么用的

检查核酸链的 O3'(i)→P(i+1) 骨架断裂。

## 什么时候用它

RNA/DNA 设计的拓扑完整性检查。

## 基本信息

- **一句话**：O3'(i)->P(i+1) backbone breaks in nucleic-acid chains
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("rna_connectivity", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--rna_connectivity.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("rna_connectivity", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `chain` | `Optional[str]` | `None` | 要遍历的链。默认遍历所有含 C3' 原子的链。 |
| `max_bond_distance` | `float` | `2.0` | O3'(i)-P(i+1) 距离超过此值即判定为断裂。该键长约 1.6 Å。 |
| `which` | `Union[str, List[int]]` | `"last"` | 测量每行的哪个结构。要测扩散输出而不是回折结果：oracle 会按序列重建连续链，无论扩散器做了什么。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
