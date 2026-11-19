# select_diverse

## 干什么用的

按序列/结构阈值选多样性子集。

## 什么时候用它

设计出一堆相似的结果，想挑出真正不同的几个。

## 基本信息

- **一句话**：Select a diverse design subset under sequence/structure cutoffs
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("select_diverse", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--select_diverse.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("select_diverse", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `max_identity` | `float` | `0.5` | 与已保留设计相似度超过此值的设计被拒绝 |
| `target_count` | `Optional[int]` | `None` | 选够这么多个就停止；None 保留所有无冲突的设计 |
| `rank_by` | `Optional[str]` | `None` | 解决冲突时优先使用的指标列（最优者在前） |
| `rank_ascending` | `bool` | `true` | True 表示 rank_by 值越小越好（如 PAE） |
| `sequence_key` | `str` | `"sequence"` | 存放氨基酸序列的列。默认解析标准的 sequence_<CHAIN> 列以及由结构支撑的蛋白序列。 |
| `require_target` | `bool` | `false` | 无法满足 target_count 时报错，而不是仅告警 |
| `required_structure_steps` | `list[str]` | _运行时计算_ | 只选包含所有指定结构步骤输出的行（如 ['rf3']）；用于防止未经筛选的补充 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
