# hbond_metrics

## 干什么用的

算配体相互作用的氢键指标。

## 什么时候用它

评估结合模式是否有足够氢键。**本机不可用**——缺 hbplus 可执行文件。

## 基本信息

- **一句话**：Compute hydrogen bond metrics for ligand interactions
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("hbond_metrics", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--hbond_metrics.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("hbond_metrics", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `atom_groups` | `Optional[dict[str, list[str]]]` | `None` | 组名到配体原子名列表的映射。提供后输出中包含各组氢键计数。 |
| `verbose` | `bool` | `false` | True 时输出还包含 `pairs` 列表，给出每个氢键的原子级细节（protein_residue、protein_atom、ligand_atom、distance、role）。 |
| `hbplus_path` | `Optional[str]` | `None` | 显式指定 HBPLUS 可执行文件。在 setup 阶段解析一次并传给各 worker，避免依赖 worker 本地设置。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
