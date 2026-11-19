# protein_hunter

## 干什么用的

Boltz 结构幻觉做从头 binder 设计。

## 什么时候用它

bindcraft 之外的另一个端到端 binder 设计方案。

## 基本信息

- **一句话**：De novo binder design via Boltz structure hallucination
- **执行方式**：纯 Python
- **需要上游输入**：否（源 block）

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("protein_hunter", inputs="<输入路径>", <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--protein_hunter.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("protein_hunter", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `command_template` | `Optional[List[str]]` | `None` | — |
| `cloud` | `bool` | `false` | — |
| `protein_seqs` | `str` | `""` | 靶点蛋白序列。多条链用 ':' 分隔。 |
| `ligand_ccd` | `str` | `""` | 小分子靶点的 CCD 代码（如 'SAM'）。 |
| `ligand_smiles` | `str` | `""` | 小分子靶点的 SMILES 字符串。 |
| `nucleic_seq` | `str` | `""` | DNA/RNA 靶点序列。 |
| `nucleic_type` | `str` | `"dna"` | 核酸类型：'dna' 或 'rna'。 |
| `num_designs` | `int` | `10` | 独立设计轨迹数。 |
| `num_cycles` | `int` | `5` | 每条轨迹的预测-重设计循环次数。 |
| `emit_all_cycles` | `bool` | `false` | 每个预测循环输出一行，而不是每条轨迹输出一行多结构谱系。需要对每个中间循环独立打分时用这个。 |
| `min_protein_length` | `int` | `100` | binder 最小长度（残基数）。 |
| `max_protein_length` | `int` | `150` | binder 最大长度（残基数）。 |
| `percent_X` | `int` | `90` | 初始序列中 X（未知）残基的百分比。 |
| `seq` | `str` | `""` | 起始 binder 序列（refiner 模式用）。留空表示随机。 |
| `refiner_mode` | `bool` | `false` | 精修 seq 提供的序列，而不是从头初始化 binder 轨迹。 |
| `msa_mode` | `str` | `"mmseqs"` | MSA 模式：'mmseqs' 或 'single'。 |
| `boltz_model_version` | `str` | `"boltz2"` | Boltz 模型版本。 |
| `diffuse_steps` | `int` | `200` | 扩散步数。 |
| `recycling_steps` | `int` | `3` | recycle 轮数。 |
| `high_iptm_threshold` | `float` | `0.8` | 保存设计的 ipTM 阈值。 |
| `high_plddt_threshold` | `float` | `0.8` | 保存设计的 pLDDT 阈值。 |
| `cyclic` | `bool` | `false` | 启用环肽设计。 |
| `alanine_bias` | `bool` | `false` | 设计时施加负丙氨酸偏置。 |
| `randomly_kill_helix_feature` | `bool` | `false` | 扩散时扰动 binder 的 i/i+4 pair 特征，减少 α 螺旋塌缩并探索其他拓扑。 |
| `negative_helix_constant` | `float` | `0.2` | 开启 randomly_kill_helix_feature 时 i/i+4 pair 特征随机负缩放的幅度。 |
| `omit_AA` | `str` | `"C"` | 设计中排除的氨基酸（如 'C'）。 |
| `temperature` | `float` | `0.1` | LigandMPNN 采样温度。 |
| `contact_residues` | `str` | `""` | 接触规格用到的靶点链残基位置。逗号分隔，多链用竖线分隔（如 '1,2,5\|3,10'）。 |
| `template_path` | `str` | `""` | 模板条件化用的 PDB 代码或路径。 |
| `template_cif_chain_id` | `str` | `""` | mmCIF 模板的链 ID。 |
| `ccd_path` | `str` | _运行时计算_ | Boltz 的 CCD 分子数据目录（.pkl 文件）路径。 |
| `boltz_model_path` | `str` | _运行时计算_ | Boltz 模型 checkpoint 路径。 |
| `gpu_id` | `int` | `0` | GPU 设备 ID。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
