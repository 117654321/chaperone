# ppi_ddg

## 干什么用的

FastRelax + ddG 算蛋白-蛋白结合能。

## 什么时候用它

物理层面的 binder 排序。注意：和 AF3 的 ipTM 排序经常不一致。

## 基本信息

- **一句话**：Protein-protein binding energy with FastRelax + ddG
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("ppi_ddg", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--ppi_ddg.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("ppi_ddg", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `binder_chain` | `str` | `"A"` | binder 的链 ID（计算未结合分数时平移到远处）。 |
| `target_chain` | `str` | `"B"` | 靶点的链 ID（保持原位）。 |
| `relax_rounds` | `int` | `1` | FastRelax 的 standard_repeats。1 很快（CPU 上约 1-3 分钟/结构）；3-5 能量更低、更收敛。 |
| `replicates` | `int` | `1` | 独立的 relax + ddG 循环次数。报告均值和标准差。每增加一次重复就多一次完整 relax。 |
| `constrain_to_start_coords` | `bool` | `true` | FastRelax 期间的调和坐标约束——让骨架贴近 AF3 预测的几何。 |
| `constraint_weight` | `float` | `1.0` | 坐标约束权重。越高越贴近输入坐标；越低松弛自由度越大。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
