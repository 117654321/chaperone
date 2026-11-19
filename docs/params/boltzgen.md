# boltzgen

## 干什么用的

BoltzGen 蛋白设计：扩散生成骨架 + 逆向折叠 + 结构验证。

## 什么时候用它

要一条龙设计流程，且想用 Boltz 生态。

## 基本信息

- **一句话**：BoltzGen protein design block
- **执行方式**：容器（`boltzgen`）
- **需要上游输入**：否（源 block）
- **容器入口**：`boltzgen`

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("boltzgen", inputs="<输入路径>", <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--boltzgen.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("boltzgen", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `command_template` | `Optional[List[str]]` | `None` | — |
| `cloud` | `bool` | `false` | — |
| `config` | `str` | **必填** | BoltzGen 设计规格 YAML 文件路径 |
| `protocol` | `str` | `"protein-anything"` | 上游 BoltzGen 运行时支持的设计协议 |
| `num_designs` | `int` | `100` | 生成的设计总数 |
| `budget` | `int` | `30` | 过滤后的最终设计数 |
| `steps` | `Optional[list[str]]` | `None` | 要运行的流水线步骤（默认全部）。可选：design、inverse_folding、design_folding、folding、affinity、analysis、filtering |
| `diffusion_batch_size` | `Optional[int]` | `None` | 每次 trunk 运行的设计数（默认 auto） |
| `step_scale` | `Optional[float]` | `None` | 固定的扩散步长缩放 |
| `noise_scale` | `Optional[float]` | `None` | 固定的噪声缩放 |
| `skip_inverse_folding` | `bool` | `false` | 跳过逆向折叠步骤 |
| `inverse_fold_num_sequences` | `int` | `1` | 每个骨架的序列数 |
| `alpha` | `Optional[float]` | `None` | 质量与多样性的权衡（0.0 偏质量，1.0 偏多样性） |
| `devices` | `Optional[int]` | `None` | GPU 数量（默认全部可用） |
| `reuse` | `bool` | `false` | 复用前次运行的结果 |
| `n_batches` | `int` | `1` | 独立 BoltzGen 运行次数 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
