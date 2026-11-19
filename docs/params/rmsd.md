# rmsd

## 干什么用的

算两个结构之间的对齐 RMSD（骨架、全原子、motif）。

## 什么时候用它

验证设计有没有被预测复现——骨架 RMSD 大说明预测跑偏了。

## 基本信息

- **一句话**：Compute alignment RMSD metrics between two designs
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("rmsd", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--rmsd.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("rmsd", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `which` | `List[int]` | `[0, -1]` | 从每行 structures 列表中选两个待比较结构的下标。默认 [0, -1] 比较第一个与最后一个。用 [-2, -1] 比较倒数第二个（如打包设计）与最后一个（预测）。 |
| `alignment_methods` | `List[data.schema.SELECTIONS]` | `[<SELECTIONS.BKBN: 'bkbn'>, <SELECTIONS.MOTIF_BKBN: 'motif_bkbn'>]` | 用于计算对齐变换的选择项列表 |
| `rmsd_targets` | `List[data.schema.SELECTIONS]` | `[<SELECTIONS.BKBN: 'bkbn'>, <SELECTIONS.MOTIF_ALLATOM: 'motif_allatom'>, <SELECTIONS.LIGANDS: 'ligand'>]` | 对齐后计算 RMSD 的选择项列表 |
| `resolve_symmetries` | `bool` | `true` | 全原子 RMSD 是否解析自同构（automorphism） |
| `select_mask_by_name_pairing` | `List[data.schema.SELECTIONS]` | `[<SELECTIONS.LIGANDS: 'ligand'>]` | RMSD 目标列表；其中的原子遮罩通过查找共同原子（按 chain_id、res_id、atom_name）配对，而不要求遮罩大小一致。两结构残基编号不同时有用。 |
| `component_remap` | `dict[str, str] \| None` | `None` | 为配体查找重映射组分名（如 {'LIG_B': 'B;N'}）。上游工具重命名配体、且 RMSD 在 SLURM worker 上运行时需要。 |
| `atom_groups` | `Optional[dict[str, list[str]]]` | `None` | 组名到配体原子名列表的映射。提供后输出中包含各组配体 RMSD。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
