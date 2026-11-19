# filter

## 干什么用的

按指标阈值或分位数筛行。

## 什么时候用它

流水线里最常用的收尾步骤。支持 min/max 阈值、分位数、每个上游设计各取最优。

## 基本信息

- **一句话**：Filter pipeline rows by metrics predicate
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("filter", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--filter.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("filter", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `expr` | `Optional[str]` | `None` | 对指标键的布尔过滤表达式，支持 and/or/not 和括号，例：'af3.min_pae_interaction <= 10 and (h.nicotinamide >= 2 or a.num_aromatic_neighbors >= 2)'。编译为 Polars 表达式。 |
| `filter_groups` | `Optional[dict[str, dict[str, blocks.util_blocks.filter.Metri` | `None` | 按名分组的过滤器集合，组间为 OR 逻辑。组内按 'filter_groups_inner_operator' 组合；各组之间 OR。再与基础 'filters' 做 AND。 |
| `filter_groups_inner_operator` | `Literal['and', 'or']` | `"and"` | 各 filter_group 内过滤器在组间 OR 之前的组合方式。 |
| `function` | `Optional[Callable[[dict], bool]]` | `None` | 谓词函数：metrics dict -> bool（True 保留） |
| `check_column_exists_only` | `bool` | `false` | True 时只校验过滤列存在且为有效浮点数（非 NaN），不真正筛行。适合用最少数据做端到端测试。 |

## `filters`

指标键 -> MetricFilter(min/max)。走 Polars 原生快路径。

指标阈值，值是 `MetricFilter` 对象。YAML 里用简写，Python 里直接构造：

```python
from blocks.util_blocks.filter import MetricFilter

Filter(filters={
    "af3.plddt": MetricFilter(min=70.0),
    "af3.min_pae_interaction": MetricFilter(max=2.0),
    "mpnn.overall_confidence": MetricFilter(
        quantile=0.125, quantile_direction="higher", parent_based=True),
})
```

| 字段 | 作用 |
|---|---|
| `min` / `max` | 阈值上下界 |
| `quantile` | 取分位，如 0.25 = 前 25% |
| `quantile_direction` | `higher` = 值越大越好 |
| `parent_based` | true = 每个上游设计各取最优（不是全局排序） |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
