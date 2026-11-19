# rfd2

## 干什么用的

RFdiffusion2：原子级蛋白设计，支持配体、小分子。

## 什么时候用它

需要配体上下文的设计。输入必须带 ORI 残基。

## 基本信息

- **一句话**：RFdiffusion2 (rf_diffusion) block for atomic-level protein design
- **执行方式**：纯 Python
- **需要上游输入**：否（源 block）

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("rfd2", inputs="<输入路径>", <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--rfd2.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("rfd2", 参数名=值)` | 最常用 |

## 形状参数在哪

RFD2 的形状参数分两处：

block 字段：`inputs`（YAML 路径）、`num_designs`、`ckpt_path`、`raise_on_missing_trbs`。

`inputs` 指向的 YAML 常用键（Hydra 风格）：

| 键 | 作用 |
|---|---|
| `contigs` | 如 `['100']` |
| `diffuser.T` | 去噪步数 |
| `inference.input_pdb` | 必须**绝对路径** |
| `recenter` | 依赖输入里的 ORI 残基定中心 |

**注意**：输入 PDB 必须带 `ORI` HETATM，否则 recenter 报错。

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `command_template` | `Optional[List[str]]` | `None` | — |
| `cloud` | `bool` | `false` | — |
| `num_designs` | `int` | `1` | 每个 benchmark case 生成的设计数 |
| `ckpt_path` | `str` | _运行时计算_ | RFdiffusion2 checkpoint 文件路径。便携镜像默认用其内置的 RFD_173.pt。 |
| `raise_on_missing_trbs` | `bool` | `true` | 设计的 TRB 文件缺失时报错 |

## 完整例子

```yaml
# chantest.yaml
contigs: ['100']
diffuser:
  T: 50
inference:
  input_pdb: /abs/path/motif_ORI.pdb   # 绝对路径 + 必须带 ORI 残基
```

```python
engine.run("rfd2", inputs="chantest.yaml", num_designs=1)
```

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `inputs` | 你的脚本：`engine.run(..., inputs="路径")` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
