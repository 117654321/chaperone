# protenix

## 干什么用的

Protenix 结构预测。

## 什么时候用它

**AF3 的快速替代**——6.6 秒/样本，本机实测排序与 AF3 完全一致。适合先粗筛再上 AF3。

## 基本信息

- **一句话**：Protenix structure prediction
- **执行方式**：容器（`protenix`）
- **需要上游输入**：是
- **容器入口**：`protenix pred`

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("protenix", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--protenix.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("protenix", 参数名=值)` | 最常用 |

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
| `model_name` | `str` | `"protenix_base_20250630_v1.0.0"` | 模型 checkpoint 名称。可选：protenix-v2（464M，精度最高，支持 TFG）、protenix_base_20250630_v1.0.0（368M，默认，数据截至 2025 年 6 月）、protenix_base_default_v1.0.0。 |
| `seeds` | `str` | `"101"` | 逗号分隔的随机种子，每个种子做一次完全独立的预测。例：'101,102,103' 表示 3 次独立运行。 |
| `dtype` | `str` | `"bf16"` | 精度：'bf16'（更快，默认）或 'fp32'（更精确）。 |
| `use_msa` | `bool` | `false` | 启用多序列比对特征。需要通过 /databases 挂载点访问 HMMER 数据库。设计流程通常不需要 MSA，默认 False。 |
| `use_template` | `bool` | `false` | 使用模板结构做引导预测。 |
| `use_tfg_guidance` | `bool` | `false` | 扩散采样期间启用免训练引导（TFG）。TFG 在无需重训练的情况下施加几何约束（位阻、扭转、键长、成对距离）。 |
| `need_atom_confidence` | `bool` | `false` | 输出逐原子置信度分数（生成 full_data JSON）。 |
| `enable_cache` | `bool` | `true` | 缓存可共享的扩散变量以加速推理。 |
| `enable_fusion` | `bool` | `true` | 启用内核融合优化。 |
| `enable_tf32` | `bool` | `true` | 对 FP32 矩阵乘法启用 TF32（Ampere 及以上更快）。 |
| `trimul_kernel` | `str` | `"cuequivariance"` | 三角乘法内核：'cuequivariance' 或 'torch'。 |
| `triatt_kernel` | `str` | `"cuequivariance"` | 三角注意力内核：'cuequivariance'、'deepspeed'、'triattention' 或 'torch'。 |
| `cache_dir` | `str` | _运行时计算_ | Protenix 模型权重目录（首次运行自动下载）。 |
| `template_json` | `Optional[str]` | `None` | Protenix 模板 JSON 路径。提供后把上游设计的蛋白序列填入该模板，同时保留配体、约束等模板设置。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
