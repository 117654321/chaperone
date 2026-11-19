# foldseek

## 干什么用的

用 Foldseek 按结构相似度聚类。

## 什么时候用它

设计出一堆骨架，想去重或选出结构多样的子集。

## 基本信息

- **一句话**：Cluster structures by structural similarity using Foldseek
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("foldseek", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--foldseek.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("foldseek", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `foldseek_exec` | `str` | _运行时计算_ | foldseek 可执行文件路径 |
| `tm_thresholds` | `List[float]` | `[0.5, 0.6, 0.7, 0.8]` | 聚类的 TM-score 阈值。每个阈值输出为 cluster_id.<threshold> 和 n_clusters.<threshold>。 |
| `alignment_type` | `int` | `1` | 1=仅结构，2=结构+序列 |
| `min_seq_id` | `float` | `0.0` | 聚类所需最小序列一致性（仅 alignment_type=2） |
| `multimer_tm_threshold` | `float` | `0.65` | 多聚体聚类的 TM 阈值 |
| `interface_lddt_threshold` | `float` | `0.65` | 多聚体聚类的界面 lDDT 阈值 |
| `chains` | `Optional[List[str]]` | `None` | 参与聚类的链 ID。None 用全部链。 |
| `group_by_task` | `bool` | `true` | True 时在每个任务组内分别聚类（用首个结构的 metadata.task 字段）。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
