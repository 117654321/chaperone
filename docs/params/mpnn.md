# mpnn

## 干什么用的

LigandMPNN / ProteinMPNN 逆向折叠：给骨架设计序列。

## 什么时候用它

流水线里最常用的序列设计步骤。支持固定残基、氢键保持、芳香保持。

## 基本信息

- **一句话**：Inverse folding with LigandMPNN (protein, ligand, soluble and membrane models)
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("mpnn", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--mpnn.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("mpnn", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `command_template` | `Optional[List[str]]` | `None` | — |
| `cloud` | `bool` | `false` | — |
| `model_type` | `Literal['protein_mpnn', 'ligand_mpnn', 'soluble_mpnn', 'per_` | `"ligand_mpnn"` | 模型族：protein_mpnn、ligand_mpnn、soluble_mpnn 或膜蛋白模型（per_residue_label_membrane_mpnn、global_label_membrane_mpnn）。 |
| `noise_level` | `Optional[Literal[0.02, 0.05, 0.1, 0.2, 0.3]]` | `None` | checkpoint 版本：模型训练时的骨架噪声（Å）。None 用上游默认值。有效值取决于 model_type（protein_mpnn 与 soluble_mpnn 等）。 |
| `num_seq_per_pdb` | `int` | `8` | 每个结构生成的序列数 |
| `output_mode` | `Literal['sequences', 'structures']` | `"sequences"` | 返回紧凑序列行（默认）或带侧链的打包结构。序列模式不打包。 |
| `preserve_fixed_coordinates` | `bool` | `true` | 打包结构且 repack_everything=0 时，从暂存输入恢复固定蛋白残基的已观测重原子坐标。新补齐的原子保留 packer 给出的坐标。 |
| `skip_existing` | `bool` | `true` | 输出已存在则跳过处理 |
| `device` | `str \| None` | `None` | 强制 MPNN 推理设备（如 'cpu'）。默认自动检测。 |
| `keep_motif_sequences_fixed` | `bool` | `true` | 保持 motif 序列固定（如果已读入 dataframe） |
| `fix_interface_residues` | `bool` | `false` | 固定界面处的序列 |
| `hbond_fix` | `bool` | `false` | 固定参与氢键的残基 |
| `aromatic_fix` | `bool` | `false` | 固定配体附近的芳香残基 |
| `component_remap` | `dict[str, str] \| None` | `None` | MPNN 之前重映射 CIF 中的残基名。旧 -> 新（如 {'LIG_B': 'B;N'}）。 |

## `args`

LigandMPNN/ProteinMPNN 的 CLI 参数。部分覆盖时其余保持默认。

可设的子参数：

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `temperature` | `float` | `0.1` | 采样温度。越低越保守（越贴近原生序列），越高越多样。 |
| `seed` | `int` | `0` | 随机种子，同时作用于 torch / numpy / python random。 |
| `batch_size` | `int` | `1` | 单次前向生成的序列数。 |
| `number_of_batches` | `int` | `1` | 运行多少个 batch。 |
| `omit_AA` | `str` | `"X"` | 设计中排除的氨基酸（如 'XC'）。X 总是被排除。加 'C' 可避免游离半胱氨酸。 |
| `bias_AA` | `str` | `""` | 逐氨基酸的 logit 偏置，如 'A:-1.024,P:2.34,C:-12.34'。负值降低该残基出现概率。 |
| `bias_AA_per_residue` | `str` | `""` | 残基级氨基酸偏置的 JSON 路径，如 {"A12": {"G": -0.3, "C": -2.0}}。 |
| `fixed_residues` | `str` | `""` | 保持固定的残基，空格分隔，如 'A12 A13 B2'。 |
| `redesigned_residues` | `str` | `""` | 要重新设计的残基（其余全固定），空格分隔，如 'A12 A13 B2'。 |
| `chains_to_design` | `str` | `""` | 要重新设计的链 ID，逗号分隔，其余链保持固定，如 'A,B'。 |
| `parse_these_chains_only` | `str` | `""` | 只从输入结构中解析这些链，逗号分隔，如 'A,B'。 |
| `symmetry_residues` | `str` | `""` | 对称残基分组，如 'A12,A13,A14\|C2,C3\|A5,B6'。组内残基保持对称。 |
| `symmetry_weights` | `str` | `""` | 与 symmetry_residues 对应的权重，如 '1.01,1.0,1.0\|-1.0,2.0'。 |
| `homo_oligomer` | `int` | `0` | 1 = 同源寡聚体设计时自动设置对称并等权。 |
| `ligand_mpnn_use_atom_context` | `int` | `1` | 1 = 使用非蛋白原子（配体等）作为上下文，0 = 忽略。 |
| `ligand_mpnn_cutoff_for_score` | `float` | `8.0` | 打分的蛋白-上下文原子距离截断（Å）。 |
| `ligand_mpnn_use_side_chain_context` | `int` | `1` | 1 = 用固定残基的侧链原子作为配体上下文。 |
| `pack_side_chains` | `int` | `1` | 侧链打包开关。output_mode='sequences' 时强制为 0；'structures' 时必须为 1。 |
| `checkpoint_path_sc` | `str` | `"/opt/ligandmpnn/model_params/ligandmpnn_sc_v_32_002_16.pt"` | 侧链打包器权重路径。默认用镜像内置官方 checkpoint；自定义宿主文件在 output_mode='structures' 时只读挂载。 |
| `number_of_packs_per_design` | `int` | `4` | 每个设计的独立侧链打包采样次数。 |
| `repack_everything` | `int` | `0` | 1 = 重打包全部残基（含固定残基）；0 = 保留固定残基的侧链。 |
| `pack_with_ligand_context` | `int` | `1` | 1 = 侧链打包时使用配体上下文。 |
| `sc_num_denoising_steps` | `int` | `3` | 侧链打包的去噪 / recycle 步数。 |
| `sc_num_samples` | `int` | `16` | 从混合分布采样，保留似然最高的样本。 |
| `packed_suffix` | `str` | `"_"` | 打包后 PDB 文件名的后缀。 |
| `zero_indexed` | `int` | `1` | 1 = 输出 PDB 从 0 开始编号。 |
| `force_hetatm` | `int` | `1` | 1 = 输出 PDB 中把配体原子写成 HETATM。 |
| `save_stats` | `int` | `0` | 1 = 保存输出统计。 |
| `file_ending` | `str` | `""` | 输出文件名附加的后缀。 |
| `verbose` | `int` | `1` | 日志详细程度。 |
| `transmembrane_buried` | `str` | `""` | per_residue_label_membrane_mpnn 的埋藏残基，空格分隔，如 'A12 A13 B2'。 |
| `transmembrane_interface` | `str` | `""` | per_residue_label_membrane_mpnn 的界面残基，空格分隔，如 'A12 A13 B2'。 |
| `global_transmembrane_label` | `int` | `0` | global_label_membrane_mpnn 的全局标签。1 = 跨膜，0 = 可溶。 |
| `parse_atoms_with_zero_occupancy` | `int` | `0` | 1 = 解析输入 PDB 中占据率为 0 的原子。 |

嵌套的 CLI 参数字典，传给上游工具（LigandMPNN / ProteinMPNN 自身）：

```python
args={"number_of_packs_per_design": 1, "temperature": 0.1}
```

**坑**：`temperature` 这类参数在 `args` 里，不在 block 顶层。
写到顶层会因 `extra_forbidden` 报错（这个 block 显式禁止了额外字段）。

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
