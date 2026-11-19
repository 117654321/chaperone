# remap_ligand

## 干什么用的

把预测输出的配体原子/残基名改成和参考 CIF 一致。

## 什么时候用它

预测器重命名了配体（AF3 常见），下游要按名字匹配时。

## 基本信息

- **一句话**：Rename predicted ligand atom/residue names to match a reference CIF
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("remap_ligand", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--remap_ligand.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("remap_ligand", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `reference_cif` | `str` | **必填** | 仅含配体、带规范原子名和 _chem_comp_bond 记录的 CIF 路径。 |
| `target_name` | `Optional[str]` | `None` | 输出中期望的残基名（如 'B;N'）。None 时从参考 CIF 读取。 |
| `atom_name_mapping` | `Optional[dict[str, str]]` | `None` | 可选的显式「预测->参考」原子名映射。提供后跳过图发现，并用映射的完整源/目标原子集校验每一行。 |
| `core_atoms` | `Optional[list[str]]` | `None` | 刚性核心的参考原子名。给定后，子结构匹配打分用的 RMSD 只在这些原子上计算，忽略柔性连接区。 |
| `buried_atoms` | `Optional[list[str]]` | `None` | core_atoms 的向后兼容别名。 |
| `sample_size` | `int` | `64` | 先扫描这么多个结构，其余再流式处理。 |
| `rmsd_ok` | `float` | `2.0` | 遇到第一个 RMSD 低于该阈值（Å）的映射就停止。 |
| `num_workers` | `Optional[int]` | `0` | 原子映射扫描的并行 worker 数。0（默认）为串行——可避免在 1 CPU 的 SLURM 分配里、torch/numba 已加载后 fork() 死锁。 |
| `emit_metric` | `bool` | `true` | 在每个重映射行上把匹配 RMSD 存到 '<name>.match_rmsd'。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
