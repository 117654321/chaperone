# rfd3_partial

## 干什么用的

RFdiffusion3 部分扩散：从已有结构出发，加噪声再生成，做多样化或细化。

## 什么时候用它

已有不错的骨架，想微调或生成变体。partial_t 控制偏离程度。

## 基本信息

- **一句话**：RFdiffusion3 partial diffusion
- **执行方式**：容器（`foundry`）
- **需要上游输入**：是
- **容器入口**：`rfd3 design`

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("rfd3_partial", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--rfd3_partial.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("rfd3_partial", 参数名=值)` | 最常用 |

## 形状参数在哪

与 rfd3 同一套 JSON 结构。

主开关是 `partial_t`：噪声强度（Å），越大偏离输入越远，推荐 ≤15。`None` 表示不启用部分扩散，退化成普通生成。

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `command_template` | `Optional[List[str]]` | `None` | — |
| `cloud` | `bool` | `false` | — |
| `compile_model` | `Optional[bool]` | `None` | 编译热点扩散模块；None 继承 Foundry 运行时的默认值。 |
| `ckpt_path` | `Optional[str]` | _运行时计算_ | checkpoint 路径（可选；foundry 会自行管理 checkpoint） |
| `json_keys_subset` | `list` | _运行时计算_ | 从 json 中取出的键 |
| `jitter_ori_sigma` | `float` | `0` | 按此标准差抖动噪声云的原点 |
| `batch_size` | `int` | `8` | 每批扩散的设计数 |
| `n_batches` | `int` | `2` | 总共运行的扩散批次数 |
| `convert_config_to_test_config` | `bool` | `false` | True 时把生成蛋白缩短到 50 残基并使用快速推理设置，用于测试。只缩短不含 'contig' 或 'partial' 规格的任务。 |
| `inference_sampler` | `dict` | _运行时计算_ | 要覆盖的采样器参数（不能经 CLI 配置） |
| `seed_offset` | `Optional[int]` | `42` | 每个 chunk 从 offset 起把种子加 1 |
| `partial_t` | `int` | `5` | 部分扩散的时间步（如 5 表示约 80% 已扩散）。 |
| `partial_diffusion_mode` | `str` | `"indexed"` | 部分扩散的模式 |
| `ligand_name` | `Optional[str]` | `None` | 部分扩散规格的配体名（如 'LIG_B'）。设置后覆盖元数据中的配体。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `inputs` | 你的脚本：`engine.run(..., inputs="路径")` |
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
