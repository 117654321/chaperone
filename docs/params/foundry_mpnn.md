# foundry_mpnn

## 干什么用的

Foundry 版 MPNN 逆向折叠（ProteinMPNN / LigandMPNN / SolubleMPNN）。

## 什么时候用它

同 mpnn，但走 Foundry 生态。与 mpnn（LigandMPNN 镜像）的数值等价性未验证。

## 基本信息

- **一句话**：Foundry MPNN for inverse folding
- **执行方式**：容器（`foundry`）
- **需要上游输入**：是
- **容器入口**：`mpnn`

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("foundry_mpnn", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--foundry_mpnn.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("foundry_mpnn", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `command_template` | `Optional[List[str]]` | `None` | — |
| `cloud` | `bool` | `false` | — |
| `model_type` | `Literal['protein_mpnn', 'ligand_mpnn']` | `"ligand_mpnn"` | 模型类型：protein_mpnn 或 ligand_mpnn。 |
| `checkpoint_path` | `Optional[str]` | `None` | 模型 checkpoint 路径。None 用 foundry 默认值。 |
| `num_seq_per_pdb` | `int` | `8` | 每个结构生成的序列数。 |
| `output_mode` | `Literal['sequences', 'structures']` | `"sequences"` | 返回紧凑的序列行，或旧版生成的 CIF 结构。 |
| `temperature` | `float` | `0.1` | 采样温度。越低越保守（越贴近原生序列），越高越多样。 |
| `seed` | `Optional[int]` | `None` | 可复现用的随机种子。 |
| `fixed_residues` | `Optional[list[str]]` | `None` | 保持固定的残基，如 ['A12', 'A13']。 |
| `designed_residues` | `Optional[list[str]]` | `None` | 要重新设计的残基（其余全固定）。 |
| `fixed_chains` | `Optional[list[str]]` | `None` | 保持固定的链 ID。 |
| `designed_chains` | `Optional[list[str]]` | `None` | 要重新设计的链 ID。 |
| `keep_motif_sequences_fixed` | `bool` | `true` | 保持 motif 序列固定（来自 RFD3 元数据）。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
