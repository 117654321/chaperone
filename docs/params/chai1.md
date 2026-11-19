# chai1

## 干什么用的

Chai-1 结构预测。

## 什么时候用它

AF3 的另一个替代。本机实测单样本偏保守（iPTM 偏低），多采样或开 MSA 后再判断。

## 基本信息

- **一句话**：Chai-1 structure prediction
- **执行方式**：容器（`chai1`）
- **需要上游输入**：是
- **容器入口**：`chai-lab fold`

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("chai1", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--chai1.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("chai1", 参数名=值)` | 最常用 |

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
| `seed` | `Optional[int]` | `None` | 可复现用的随机种子。None 为随机。 |
| `use_esm_embeddings` | `bool` | `true` | 对蛋白使用 ESM 嵌入。 |
| `use_msa_server` | `bool` | `false` | 通过 ColabFold mmseqs2 服务器自动生成 MSA。 |
| `msa_server_url` | `Optional[str]` | `None` | MSA 服务器地址（默认 ColabFold）。 |
| `low_memory` | `bool` | `true` | 使用省内存的推理模式。 |
| `cache_dir` | `Optional[str]` | _运行时计算_ | Chai-1 模型权重目录。默认取 CHAI_DOWNLOADS_DIR 设置。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
