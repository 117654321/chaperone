# select_motif

## 干什么用的

用自定义函数挑 motif 残基，供下游固定。

## 什么时候用它

需要复杂规则确定哪些残基算 motif 时。

## 基本信息

- **一句话**：Apply a function to select motif residues for downstream fixing
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("select_motif", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--select_motif.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("select_motif", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `selector` | `Optional[Callable[[data.structure.LoadedStructure], list[str` | `None` | 函数：LoadedStructure -> 要固定的残基 ID 列表 |
| `metadata_key` | `str` | `"motif"` | 把选中残基写入的元数据键 |
| `append` | `bool` | `true` | 追加到已有元数据键（True）或覆盖（False） |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
