# clash

## 干什么用的

数骨架重原子之间的非成键碰撞。

## 什么时候用它

快速筛查设计质量，碰撞多的直接淘汰。

## 基本信息

- **一句话**：Count non-bonded backbone heavy-atom clashes
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("clash", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--clash.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("clash", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `cutoff` | `float` | `1.5` | 非成键骨架原子对间距小于此值（Å）即计为碰撞。 |
| `backbone_only` | `bool` | `true` | 只统计骨架重原子（N/CA/C/O）。设为 False 用全部重原子——但不同生成器侧链完整度不同（如聚甘氨酸 vs 全原子骨架），结果不可直接比较。 |
| `sequence_separation` | `int` | `1` | 同链中相隔不超过此值的残基视为成键并排除。取 1 表示排除残基内和相邻残基对。 |
| `exclude_hetero` | `bool` | `true` | 打分前丢弃 hetero（配体/辅因子）原子。配体是标准氨基酸时必须开启——例如鸟氨酸（ORN）能通过 filter_amino_acids，会贡献假骨架。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
