# af3

## 干什么用的

AlphaFold3 结构预测。吃序列或结构，输出预测的三维结构和置信度指标（pLDDT、pTM、ipTM、PAE）。

## 什么时候用它

验证设计的可折叠性，或者给复合物打分。最准但最慢（约 47 秒/样本），需要 411G 数据库。

## 基本信息

- **一句话**：AlphaFold3 structure prediction
- **执行方式**：容器（`alphafold3`）
- **需要上游输入**：是
- **容器入口**：`python /opt/chaperone-runtime-scripts/run_alphafold_AF.py --run_data_pipeline=False --run_inference=True --db_dir=/databases --model_dir=/databases/alphafold`

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("af3", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--af3.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("af3", 参数名=值)` | 最常用 |

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
| `jax_cache_dir` | `Optional[str]` | _运行时计算_ | 直接挂进容器的可写编译缓存 |
| `input_mode` | `Literal['auto', 'mmcif', 'json']` | `"mmcif"` | AF3 输入准备模式。默认 'mmcif' 序列化完整 AtomArray 并用 AF3 原生 Input.from_mmcif 转换。'json' 用于旧版仅 JSON 的选项，'auto' 在输入带模板时选 JSON。 |
| `input_preparation_version` | `Literal[2]` | `2` | 序列权威输入与多种子清单的内部缓存版本号；非用户选项。 |
| `use_local_msas` | `bool` | `false` | 把磁盘 MSA 库里各蛋白链预计算的 a3m 注入 AF3 输入。原生 mmCIF 和旧版 JSON 两种输入模式都支持。 |
| `msa_dirs` | `Optional[list]` | `None` | 按顺序搜索的分片 MSA 根目录，可为路径或 {"dir", "extension", "directory_depth"} dict。None 用 PROTEIN_MSA_DIRS。 |
| `max_msa_sequences` | `Optional[int]` | `10000` | 注入的 MSA 截断到此深度。 |
| `raise_if_missing_msa_for_protein_of_length_n` | `Optional[int]` | `None` | 长度不小于此值的蛋白若没有磁盘 MSA 就报错，而不是静默退回单序列模式。 |
| `template_json` | `Optional[str]` | `None` | AF3 输入的模板 JSON 路径。不提供则从零构建输入。 |
| `add_ptm_at_mapped_residues` | `Optional[dict]` | `None` | 共价修饰的 {ptmType: 原始残基键} 映射。残基键（如 'A10'）在 RFD3 的 diffused_index_map 中查找，定位到设计链中的对应位置。 |
| `add_ptm_at_residues` | `Optional[list[dict]]` | `None` | 直接加到蛋白序列上的 AF3 修饰 dict 列表。每项应含 'ptmType' 与 'ptmPosition' 键。与 add_ptm_at_mapped_residues 不同，这里的编号是设计链自身的编号。 |
| `consolidate_intermediates` | `bool` | `true` | 编译后把每个设计冗余的逐样本子目录（outputs/<design>/seed-*_sample-*/）打包成单个未压缩的 outputs/<design>/_intermediates.tar。 |
| `buckets` | `Optional[list[int]]` | `None` | JIT 编译的 token 数分桶。None 用内部脚本的智能默认（小 token 数细分，大 token 数粗分）。必须严格递增。 |
| `flash_attention_implementation` | `str` | `"triton"` | 'triton'（最快，需 Ampere 及以上）、'cudnn' 或 'xla'（可移植）。 |
| `conformer_max_iterations` | `Optional[int]` | `None` | RDKit 构象搜索最大迭代数。None 用 RDKit 默认值。 |
| `mean_pae_contact_distance` | `float` | `5.0` | `interface_mean_pae` 指标的接触截断距离（Å）：只有任一原子距配体在此距离内的蛋白残基参与计算。数值越小越聚焦最紧密的接触。 |
| `mean_pae_core_atoms` | `Optional[list[str]]` | `None` | 为 `interface_mean_pae` 与 `full_mean_pae` 指标定义埋藏/核心子结构的配体原子名。设置后只用这些原子作为参考集。 |
| `mean_pae_sidechain_angle` | `Optional[float]` | `90.0` | 口袋残基的 CA→侧链质心向量与 CA→最近配体原子向量之间的最大夹角（度）；超过就不计入 `interface_sidechain_angle_median`。 |
| `model_seeds` | `list[int]` | _运行时计算_ | 写入每个输入 JSON 的独立 AF3 模型种子。多种子会重跑 trunk 与扩散推理，适合真正的重复实验；diffusion_batch_size 是在一次 trunk 内多次采样，更省。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
