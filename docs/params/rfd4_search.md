# rfd4_search

## 基本信息

- **一句话**：RFD4 reward-guided beam search with an AF3 refolding oracle
- **执行方式**：纯 Python
- **需要上游输入**：否（源 block）

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("rfd4_search", inputs="<输入路径>", <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--rfd4_search.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("rfd4_search", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `search_config` | `Optional[str]` | `None` | Path to a beam-search experiment YAML (an ``inference_experiment`` config). None uses the checkout's ``inference_beam_example``. |
| `ckpt_path` | `Optional[str]` | `None` | Local model bundle. Search must not download weights: the oracle spawns containers on a host that is typically offline, and HF hub access fails before search starts. Defaults to RFD4_WEIGHTS_DIR. |
| `num_replicates` | `int` | `1` | Designs to search per input. |
| `batch_size` | `int` | `1` | Sampler batch size. |
| `seed` | `Optional[int]` | `None` | Base seed. |
| `output_subdir` | `str` | `"search_run"` | Directory under the block sandbox for RFD4 output. |

## `extra_overrides`

Extra Hydra overrides, e.g. ['search.beam_width=4'].

| 项 | 作用 |
|---|---|
| `key=value` | 键已存在，直接覆盖 |
| `+key=value` | 键不存在，新增 |
| `++key=value` | 键存在但 struct 不允许覆盖，强制写 |

传的是**字符串列表**，每项原样拼进上游命令行：

```python
extra_overrides=["recycle_strategy=thinking_high", "++generation.args.nsteps=100"]
```

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `inputs` | 你的脚本：`engine.run(..., inputs="路径")` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
