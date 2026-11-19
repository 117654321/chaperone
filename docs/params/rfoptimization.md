# rfoptimization

## 干什么用的

RF3 梯度 / Boltz-2 循环 + 外部 MPNN 序列重设计。

## 什么时候用它

迭代优化已有设计：多轮预测-重设计，每轮用梯度或预测器打分选优。

## 基本信息

- **一句话**：RF3 gradient / Boltz-2 cycling with external MPNN sequence redesign
- **执行方式**：容器（`rfoptimization`）
- **需要上游输入**：是
- **容器入口**：`/opt/rfo-env/bin/python -c import json, subprocess, sys
for config in json.load(open(sys.argv[1])):
    subprocess.run(['/opt/rfo-env/bin/rfo', '--config', config], check=True)
`

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("rfoptimization", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--rfoptimization.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("rfoptimization", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `command_template` | `Optional[List[str]]` | `None` | — |
| `cloud` | `bool` | `false` | — |
| `total_cycles` | `int` | `10` | 每个输入的 RF3/Boltz + MPNN 循环次数。 |
| `backprop_fraction` | `float` | `0.5` | 每轮使用 RF3 梯度的概率；否则用 Boltz-2。 |
| `mpnn_model_type` | `Literal['protein_mpnn', 'ligand_mpnn']` | `"protein_mpnn"` | — |
| `mpnn_temperature` | `float` | `0.1` | — |
| `seed` | `int` | `42` | — |
| `rf3_checkpoint` | `str \| None` | `None` | 公开的带置信度 RF3 checkpoint；使用 RF3 时必需。默认用已配置的 Foundry checkpoint 目录。 |
| `boltz_cache` | `str` | _运行时计算_ | — |
| `rf3_config` | `str \| None` | `None` | 上游优化器 YAML（可选）。省略则用固定的 cycle_ppi preset。 |
| `msa_paths` | `dict[str, str]` | _运行时计算_ | 可选的「链 -> A3M 路径」映射；不使用远程 MSA 服务。 |
| `templates` | `dict[str, str]` | _运行时计算_ | RF3 分支可选的「链 -> 模板路径」映射。 |
| `cyclic` | `bool` | `false` | 只在 Boltz 中把 A 链标记为环状；RF3 不约束其闭合。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
