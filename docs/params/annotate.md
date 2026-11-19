# annotate

## 干什么用的

给结构加注释：界面残基、氢键、配体邻域芳香残基。

## 什么时候用它

下游 block（MPNN 的 aromatic_fix / hbond_fix）需要这些注释时。默认不计算，省时间。

## 基本信息

- **一句话**：Annotate molecular structures
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("annotate", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--annotate.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("annotate", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `annotations` | `list[Literal['interface', 'hbond', 'aromatics_near_ligand', ` | **必填** | 要计算的注释；显式选择以避免不必要的工作。 |
| `overwrite` | `bool` | `true` | 是否覆盖已有注释 |
| `interface_config` | `blocks.util_blocks.annotate.InterfaceConfig` | _运行时计算_ | 界面残基注释的配置 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
