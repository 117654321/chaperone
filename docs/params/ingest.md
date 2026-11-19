# ingest

## 干什么用的

从各种来源导入数据（DataFrame、CSV、Parquet、结构路径列表）。

## 什么时候用它

流水线入口，把外部数据变成管道能吃的表。

## 基本信息

- **一句话**：Ingest data from various sources
- **执行方式**：纯 Python
- **需要上游输入**：否（源 block）

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("ingest", inputs="<输入路径>", <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--ingest.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("ingest", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `compile_as` | `Optional[str]` | `None` | 提供后把 source 当作逗号分隔的目录，用指定 block（如 'rfd3'、'mpnn'）编译 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
