# peppr

## 干什么用的

用 peppr 算结构评估指标：fnat、irmsd、lrmsd、dockq、lDDT。

## 什么时候用它

有参考结构时，量化预测和参考的偏差。

## 基本信息

- **一句话**：Compute structural evaluation metrics using peppr
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("peppr", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--peppr.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("peppr", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `metrics` | `List[blocks.metrics.peppr.PepprMetric]` | `[<PepprMetric.RMSD: 'rmsd'>, <PepprMetric.TM_SCORE: 'tm_score'>, <PepprMetric.LDDT: 'lddt'>, <PepprMetric.LDDT_PLI: 'lddt_pli'>, <PepprMetric.FNAT: 'fnat'>, <PepprMetric.IRMSD: 'irmsd'>, <PepprMetric.LRMSD: 'lrmsd'>, <PepprMetric.DOCKQ: 'dockq'>]` | 要计算的指标。可选：rmsd、tm_score、lddt、lddt_pli、fnat、irmsd、lrmsd、dockq |
| `rmsd_threshold` | `float` | `2.0` | MonomerRMSD 分类的 RMSD 阈值（Å） |
| `tolerate_exceptions` | `bool` | `true` | True 时单个指标失败仍继续（如无配体时的 lDDT-PLI）。失败指标存为 None。 |
| `which` | `List[int]` | `[0, -1]` | 结构谱系中参考与预测的下标。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
