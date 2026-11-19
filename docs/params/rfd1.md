# rfd1

## 干什么用的

RFdiffusion v1：骨架层面蛋白设计。支持无条件生成、motif 支撑、binder 设计、对称设计。

## 什么时候用它

老版但稳定。contigs 参数控制长度、对称用 symmetry 字段。

## 基本信息

- **一句话**：RFdiffusion v1 backbone-level protein design
- **执行方式**：容器（`rfdiffusion1`）
- **需要上游输入**：否（源 block）
- **容器入口**：`python /opt/RFdiffusion/scripts/run_inference.py`

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("rfd1", inputs="<输入路径>", <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--rfd1.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("rfd1", 参数名=值)` | 最常用 |

## 形状参数在哪

RFD1 的形状参数**就是 block 字段**，不在 JSON 里：

| 参数 | 作用 |
|---|---|
| `contigs` | 长度与结构。`'150-150'` 无条件；`'5-15/A10-25/30-40'` 骨架支撑；`'A1-7/150/0 B1-7/150/0'` 多聚体 |
| `num_designs` | 每个 chunk 生成几个 |
| `symmetry` | `'c3'` / `'c5'` / `'d3'` / `'tetrahedral'`，会自动切到 symmetry 配置 |
| `input_pdb` | motif 支撑或 binder 设计的目标 PDB |
| `hotspot_residues` | 热点，如 `['A30','A33']` |
| `inpaint_seq` / `inpaint_str` | inpaint 的序列 / 结构位置 |
| `denoiser.noise_scale_ca` / `noise_scale_frame` | 平移 / 旋转噪声缩放 |
| `diffuser.T` | 去噪步数 |

环化：RFD1 没有独立的环化字段，通过 `contigs` 的对称表达实现。

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `command_template` | `Optional[List[str]]` | `None` | — |
| `cloud` | `bool` | `false` | — |
| `contigs` | `str` | **必填** | contig 规格。片段用 / 分隔，链用空格分隔。例：'150-150' 无条件生成；'5-15/A10-25/30-40' 骨架支撑；'A1-7/150/0 B1-7/150/0 C' 多聚体。 |
| `num_designs` | `int` | `10` | 每个 chunk 生成的设计数 |
| `input_pdb` | `Optional[str]` | `None` | motif 支撑或 binder 设计用的输入 PDB |
| `config_name` | `str` | `"base"` | Hydra 配置名（如 'base'、'symmetry'） |
| `symmetry` | `Optional[str]` | `None` | 寡聚体设计的对称类型（如 'c3'、'c5'、'd3'、'tetrahedral'）。会自动设置 config_name='symmetry'。 |
| `diffuser_T` | `int` | `50` | 去噪时间步数 |
| `partial_T` | `Optional[int]` | `None` | 部分扩散时间步数（用于增加设计多样性） |
| `noise_scale_ca` | `Optional[float]` | `None` | 平移噪声缩放（denoiser.noise_scale_ca） |
| `noise_scale_frame` | `Optional[float]` | `None` | 旋转噪声缩放（denoiser.noise_scale_frame） |
| `ckpt_override_path` | `Optional[str]` | `None` | 自定义 checkpoint 路径。默认用容器内的 Base_ckpt.pt。常用选项：Complex_base_ckpt.pt、Complex_Fold_base_ckpt.pt、ActiveSite_ckpt.pt、InpaintSeq_ckpt.pt。 |
| `hotspot_res` | `Optional[List[str]]` | `None` | binder 设计的 hotspot 残基，如 ['A30', 'A33', 'A34'] |
| `inpaint_seq` | `Optional[List[str]]` | `None` | 序列 inpaint 位置，如 ['A1', 'A30-40'] |
| `inpaint_str` | `Optional[List[str]]` | `None` | 结构 inpaint 位置（柔性区域），如 ['B165-178'] |
| `scaffold_guided` | `bool` | `false` | 启用带 ss/adj 约束的折叠条件化设计 |
| `target_pdb` | `Optional[str]` | `None` | 骨架引导 binder 设计的靶点 PDB |
| `scaffold_dir` | `Optional[str]` | `None` | 骨架引导用的 _ss.pt 与 _adj.pt 文件目录 |
| `extra_hydra_args` | `Optional[List[str]]` | `None` | 原样传入的额外 Hydra CLI 覆盖，如 ['diffuser.chi_type=interp'] |
| `raise_on_missing_trbs` | `bool` | `true` | 设计的 TRB 文件缺失时报错 |

## 完整例子

### 无条件单体

```python
engine.run("rfd1", contigs="150-150", num_designs=4, diffuser_T=50)
```

### C3 对称

```python
engine.run("rfd1", contigs="80-80", symmetry="c3", num_designs=2)
```

### motif 支撑

```python
engine.run("rfd1", contigs="5-15/A10-25/30-40", input_pdb="motif.pdb", num_designs=2)
```

### binder 设计

```python
engine.run("rfd1", contigs="100-100,/0,B1-114", hotspot_residues=["B50"], num_designs=4)
```

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
