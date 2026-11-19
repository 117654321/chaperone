# motif_geometry

## 干什么用的

算 motif 原子之间的距离和角度。

## 什么时候用它

验证催化位点、结合位点的几何关系是否保持。

## 基本信息

- **一句话**：Distances/angles between motif atoms, via diffused_index_map
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("motif_geometry", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--motif_geometry.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("motif_geometry", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `measurements` | `Dict[str, List[str]]` | **必填** | 名称 -> 原子规格，格式 '<参考残基 id>.<原子名>'，如 {'contact': ["A24.N1", "B4.O2'"]}。两个规格给出距离（Å），三个规格给出以中间原子为顶点的角度（度）。 |
| `which` | `List[int]` | `[0, -1]` | 每行 structures 列表中的两个下标：携带 diffused_index_map 的结构，以及要测量的结构。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
