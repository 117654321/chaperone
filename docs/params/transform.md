# transform

## 干什么用的

对每行应用 atomworks Transform。

## 什么时候用它

需要自定义结构变换，且已有现成的 Transform 对象时。

## 基本信息

- **一句话**：Apply an atomworks Transform to each pipeline row
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("transform", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--transform.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("transform", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `transform` | `Any` | `None` | 要应用的 atomworks Transform 实例 |
| `extract_metrics` | `Optional[list[str]]` | `None` | 从 transform 输出中提取为指标的键 |
| `extract_metadata` | `Optional[list[str]]` | `None` | 从 transform 输出中提取为元数据更新的键 |
| `write_structure` | `bool` | `false` | True 时把 result['atom_array'] 写回为新的 CIF 文件 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
