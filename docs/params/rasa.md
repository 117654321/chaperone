# rasa

## 干什么用的

算配体原子的溶剂可及表面积。

## 什么时候用它

判断配体埋藏程度——埋得深通常结合更牢。

## 基本信息

- **一句话**：Compute solvent accessible surface area for ligand atoms
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("rasa", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--rasa.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("rasa", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `atom_groups` | `Optional[dict[str, list[str]]]` | `None` | 组名到配体原子名列表的映射。提供后输出中包含各组的 RASA 汇总。 |
| `probe_radius` | `float` | `1.4` | 溶剂探针半径（Å）。 |
| `backbone_only` | `bool` | `false` | True 时在计算 SASA 前剥离蛋白侧链，使配体可及性只相对骨架原子（N、CA、C、O）度量。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
