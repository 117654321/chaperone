# rf3

## 干什么用的

RosettaFold3 结构预测。

## 什么时候用它

Foundry 生态的结构预测，速度和质量介于 Boltz 和 AF3 之间。

## 基本信息

- **一句话**：RosettaFold3 structure prediction
- **执行方式**：容器（`foundry`）
- **需要上游输入**：是
- **容器入口**：`rf3 fold`

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("rf3", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--rf3.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("rf3", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `command_template` | `Optional[List[str]]` | `None` | — |
| `cloud` | `bool` | `false` | — |
| `diffusion_batch_size` | `int` | `5` | 每个输入的扩散采样数（预测结构数）。 |
| `read_most_confident_model` | `bool` | `true` | True 只读置信度最高的模型；False 读全部样本。 |
| `n_recycles` | `Optional[int]` | `10` | — |
| `num_diffusion_steps` | `int` | `50` | — |
| `ckpt_path` | `Optional[str]` | _运行时计算_ | checkpoint 路径或 Foundry 注册名（默认 rf3）。 |
| `compile_as_metric` | `bool` | `false` | True 时把输出编译为带 path_handle 的指标，而不是 path。 |
| `remove_ligands` | `bool` | `false` | True 时输入准备阶段跳过配体。 |
| `specified_smiles` | `dict` | _运行时计算_ | 配体名 → SMILES 字符串的映射。 |
| `specified_ccd` | `dict` | _运行时计算_ | 配体名 → CCD 代码的映射。 |
| `disable_ccd_detection` | `bool` | `false` | True 时禁用自动 CCD 代码检测。 |
| `which` | `Union[List[int], str]` | `"last"` | 预测每行结构谱系里的哪几个结构。'last'（默认）用最新的；整数列表按下标选择。 |
| `sort_by_length` | `bool` | `true` | True（默认）时按 `sort_length_key` 对输入排序后再分块，让每块落在窄的 JIT bucket 区间内。无法解析该 key 时退回不排序（并告警）。 |
| `sort_length_key` | `str` | `"rfd3.num_residues"` | Metric column to sort on when sort_by_length=True (dot-path into metrics JSON, as exposed by handler.unpack()). When absent, the other `sort_length_fallbacks` keys are tried, and finally the residue count is measured from each structure file. |
| `sort_length_fallbacks` | `list[str]` | _运行时计算_ | Additional metric columns tried, in order, when sort_length_key is absent. Sorting by length only changes chunk packing, never results, so a fallback cannot alter the science. |
| `output_lineage_version` | `Literal[2]` | `2` | 完整输出与显式序列谱系的内部缓存版本号。 |
| `early_stopping_plddt_threshold` | `float` | `0.5` | 初始 recycle 后 pLDDT 低于此阈值就提前停止扩散。设为 0.5 可提升 10-20 倍吞吐，设 0 关闭。提前停止的输出不保存。 |
| `dump_trajectories` | `bool` | `false` | 写出每个样本的含噪与去噪扩散轨迹。轨迹文件很大，会把最终预测放在最后，并保留在块输出目录中。 |
| `seed_offset` | `int` | `42` | 基础随机种子；每个块加 1。设置 model_seeds 时忽略。 |
| `model_seeds` | `Optional[list[int]]` | `None` | 每个输入做多种子推理的种子列表。每个种子跑一次完全独立的 trunk，结构多样性比 diffusion_batch_size 更高。 |
| `msa_dirs` | `Optional[list[str]]` | `None` | 磁盘上蛋白 MSA 根目录的绝对路径。Chaperone 会同时导出为 LOCAL_MSA_DIRS 和 PROTEIN_MSA_DIRS（受支持的 Foundry 版本），因此 RF3 使用 MSA 不再依赖构建读哪个变量。 |
| `raise_if_missing_msa_for_protein_of_length_n` | `Optional[int]` | `None` | 长度不小于此值的蛋白若无 MSA 就报错。设为 0 表示每条蛋白链都要求有 MSA。 |
| `create_bond_graph` | `bool` | `false` | 用 specified_smiles 指定配体键并把输入写成带键拓扑的 CIF。输入结构中的配体残基名非规范时必须开启。 |
| `input_mode` | `Literal['file', 'sequence']` | `"file"` | 'file' 直接传 CIF/PDB（当前默认）。'sequence' 用序列 + CCD/SMILES 构建 RF3 组件 JSON。 |
| `template_json` | `Optional[str]` | `None` | RF3 JSON 模板路径。蛋白序列由上游设计填入；其余内容（配体、键、模板）从模板保留。 |
| `template_selection` | `Optional[list[str]]` | `None` | 聚合物和小分子的 token 级模板。使用 AtomSelection 格式，如 ['A/*/30', 'A/*/53', 'X']。 |
| `ground_truth_conformer_selection` | `Optional[list[str]]` | `None` | 把选定残基/链锁定到真值构象。适合在保留已知配体构象的同时让模型预测其周围的蛋白结构。 |
| `cyclic_chains` | `Optional[list[str]]` | `None` | 需要环化的链 ID。输入为 CIF 时环化会自动检测。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
