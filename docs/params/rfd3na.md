# rfd3na

## 干什么用的

RFdiffusion3NA：全原子蛋白/DNA/RNA 设计。

## 什么时候用它

核酸相关的设计——蛋白-RNA、蛋白-DNA 复合物。

## 基本信息

- **一句话**：RFdiffusion3NA block (all-atom protein/DNA/RNA design)
- **执行方式**：容器（`foundry`）
- **需要上游输入**：否（源 block）
- **容器入口**：`rfd3na design`

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("rfd3na", inputs="<输入路径>", <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--rfd3na.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("rfd3na", 参数名=值)` | 最常用 |

## 形状参数在哪

与 rfd3 同一套 JSON 结构，额外支持核酸。

`contig` 里核酸链加后缀：`A1-30:dna`（DNA）、`B1-40:rna`（RNA）。`cyclic_chains` 同样可用。

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `command_template` | `Optional[List[str]]` | `None` | — |
| `cloud` | `Optional[bool]` | `None` | 在暂存 RFD3NA checkpoint 之前不支持云端执行。 |
| `compile_model` | `Optional[bool]` | `None` | 编译热点扩散模块；None 继承 Foundry 运行时的默认值。 |
| `ckpt_path` | `Optional[str]` | _运行时计算_ | RFD3NA checkpoint 路径。设为 'rfd3na' 或 None 则用 Foundry 的 checkpoint 注册表/搜索路径。 |
| `json_keys_subset` | `list` | _运行时计算_ | 从 json 中取出的键 |
| `jitter_ori_sigma` | `float` | `0` | 按此标准差抖动噪声云的原点 |
| `batch_size` | `int` | `8` | 每批扩散的设计数 |
| `n_batches` | `int` | `2` | 总共运行的扩散批次数 |
| `convert_config_to_test_config` | `bool` | `false` | True 时把生成蛋白缩短到 50 残基并使用快速推理设置，用于测试。只缩短不含 'contig' 或 'partial' 规格的任务。 |
| `inference_sampler` | `dict` | _运行时计算_ | RFD3NA 推理采样器覆盖项。 |
| `seed_offset` | `Optional[int]` | `42` | 每个 chunk 从 offset 起把种子加 1 |
| `read_sequence_from_sequence_head` | `bool` | `false` | 上游 README 建议 RFD3NA 全局设为 False。 |
| `prevalidate_inputs` | `bool` | `true` | 加载模型前校验每个 RFD3NA 输入规格。 |
| `low_memory_mode` | `bool` | `false` | GPU 显存受限时使用省内存的 tokenization。 |
| `dump_trajectories` | `bool` | `false` | 写出体积较大的含噪与去噪扩散轨迹文件。 |
| `skip_existing` | `bool` | `true` | 输出文件已存在的设计跳过。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `inputs` | 你的脚本：`engine.run(..., inputs="路径")` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
