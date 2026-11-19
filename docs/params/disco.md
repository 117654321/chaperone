# disco

## 干什么用的

蛋白序列-结构联合设计，可条件化在配体上。

## 什么时候用它

设计结合小分子的蛋白（比如血红素结合蛋白）。

## 基本信息

- **一句话**：Multimodal protein sequence-structure co-design
- **执行方式**：容器（`disco`）
- **需要上游输入**：否（源 block）
- **容器入口**：`python /opt/disco/runner/inference.py`

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("disco", inputs="<输入路径>", <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--disco.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("disco", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `command_template` | `Optional[List[str]]` | `None` | — |
| `cloud` | `bool` | `false` | — |
| `num_seeds` | `int` | `5` | 随机种子数（输入 JSON 中每个 job 的样本数） |
| `experiment` | `Literal['designable', 'diverse']` | `"designable"` | 实验 preset：'designable'（可设计性更高）或 'diverse'（结构更多样） |
| `effort` | `Literal['fast', 'max']` | `"fast"` | 计算 preset：'fast'（约快 4 倍，默认）或 'max'（全质量）。条件生成用 'max'。 |
| `n_batches` | `int` | `1` | 种子分摊到的并行块数 |
| `use_deepspeed_evo_attention` | `bool` | `true` | 使用 DeepSpeed EvoformerAttention（需要 CUTLASS 和 Ampere 及以上 GPU） |
| `n_diffusion_steps` | `Optional[int]` | `None` | 覆盖扩散步数（默认由 effort preset 决定） |
| `n_cycles` | `Optional[int]` | `None` | 覆盖 recycle 轮数（默认由 effort preset 决定） |
| `noisy_guidance` | `Optional[bool]` | `None` | 开启/关闭 noisy guidance（默认由 experiment preset 决定） |
| `ckpt_path` | `Optional[str]` | `None` | 自定义模型 checkpoint 路径（默认从 HuggingFace 自动下载） |
| `cache_dir` | `str` | _运行时计算_ | 挂进容器的 HuggingFace 模型缓存 |
| `compile_cache_dir` | `str` | _运行时计算_ | 可写的 CUDA 扩展与临时构建缓存；可以放在节点本地。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `inputs` | 你的脚本：`engine.run(..., inputs="路径")` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
