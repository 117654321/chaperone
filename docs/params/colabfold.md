# colabfold

## 干什么用的

ColabFold（AlphaFold2 封装），支持 MSA 服务器和本地 MSA。

## 什么时候用它

需要 AF2 结果但不想自己搭 AF2 环境。可离线，用本地 MSA 库。

## 基本信息

- **一句话**：ColabFold (AlphaFold2) structure prediction
- **执行方式**：容器（`colabfold_portable`）
- **需要上游输入**：是
- **容器入口**：`colabfold_batch`

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("colabfold", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--colabfold.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("colabfold", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `command_template` | `Optional[List[str]]` | `None` | — |
| `cloud` | `bool` | `false` | — |
| `diffusion_batch_size` | `int` | `5` | 每个输入的扩散采样数（预测结构数）。 |
| `read_most_confident_model` | `bool` | `true` | True 只读置信度最高的模型；False 读全部样本。 |
| `n_recycles` | `Optional[int]` | `None` | trunk 回收（recycle）步数。None 用模型默认值。 |
| `num_diffusion_steps` | `int` | `200` | 扩散采样步数。 |
| `ckpt_path` | `Optional[str]` | `None` | 模型权重的 checkpoint 路径（可选）。 |
| `compile_as_metric` | `bool` | `false` | True 时把输出编译为带 path_handle 的指标，而不是 path。 |
| `remove_ligands` | `bool` | `false` | True 时输入准备阶段跳过配体。 |
| `specified_smiles` | `dict` | _运行时计算_ | 配体名 → SMILES 字符串的映射。 |
| `specified_ccd` | `dict` | _运行时计算_ | 配体名 → CCD 代码的映射。 |
| `disable_ccd_detection` | `bool` | `false` | True 时禁用自动 CCD 代码检测。 |
| `which` | `Union[List[int], str]` | `"last"` | 预测每行结构谱系里的哪几个结构。'last'（默认）用最新的；整数列表按下标选择。 |
| `sort_by_length` | `bool` | `true` | True（默认）时按 `sort_length_key` 对输入排序后再分块，让每块落在窄的 JIT bucket 区间内。无法解析该 key 时退回不排序（并告警）。 |
| `sort_length_key` | `str` | `"rfd3.num_residues"` | Metric column to sort on when sort_by_length=True (dot-path into metrics JSON, as exposed by handler.unpack()). When absent, the other `sort_length_fallbacks` keys are tried, and finally the residue count is measured from each structure file. |
| `sort_length_fallbacks` | `list[str]` | _运行时计算_ | Additional metric columns tried, in order, when sort_length_key is absent. Sorting by length only changes chunk packing, never results, so a fallback cannot alter the science. |
| `num_models` | `int` | `5` | AF2 模型数量（1-5）。 |
| `num_seeds` | `int` | `1` | 每个模型的随机种子数。 |
| `random_seed` | `Optional[int]` | `None` | 基础随机种子。None 为 ColabFold 默认值（0）。 |
| `msa_mode` | `str` | `"single_sequence"` | MSA 数据库：single_sequence（无 MSA，离线）、mmseqs2_uniref_env、mmseqs2_uniref、mmseqs2_uniref_env_envpair。 |
| `use_msa_server` | `bool` | `false` | 向 ColabFold MMseqs2 服务器查询 MSA。为 True 且 msa_mode 仍是 single_sequence 时自动切到 mmseqs2_uniref_env。计算节点需能出网。 |
| `use_local_msas` | `bool` | `false` | 在磁盘上预计算的 MSA 库里查找每条待折叠序列，取出 a3m 作为输入，会覆盖 msa_mode。完全离线。 |
| `msa_dirs` | `Optional[list]` | `None` | 按顺序搜索的分片 MSA 根目录，可为路径或 {"dir", "extension", "directory_depth"} dict。None 用站点的 PROTEIN_MSA_DIRS 设置。 |
| `max_msa_sequences` | `Optional[int]` | `10000` | 取用的 MSA 截断到此深度。None 保留库中完整条目。 |
| `raise_if_missing_msa_for_protein_of_length_n` | `Optional[int]` | `None` | 长度不小于此值的蛋白若无磁盘 MSA 就报错。None（默认）只用查询序列做比对。设为 0 表示每个输入都要求有 MSA。 |
| `model_type` | `str` | `"auto"` | AF2 模型集（auto、alphafold2_ptm、alphafold2_multimer_v3 等）。 |
| `use_templates` | `bool` | `false` | 从 MSA 服务器查询 PDB 模板（需联网）。 |
| `amber_relax` | `bool` | `false` | 运行 AMBER 弛豫（仅 CPU；从不加 --use-gpu-relax）。 |
| `rank` | `str` | `"auto"` | 模型排序指标（auto、plddt、ptm、iptm、multimer）。 |
| `data_dir` | `Optional[str]` | _运行时计算_ | AF2 参数可写目录（--data）。首次运行下载约 3-4GB。使用便携镜像时自动挂进容器。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
