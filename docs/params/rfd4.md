# rfd4

## 干什么用的

RFD4-Proteina：flow matching 生物分子设计，条件化能力最强（热点、埋藏、氢键、二级结构）。

## 什么时候用它

需要精细条件控制的 binder 设计。**长度、热点、埋藏都在 inputs 的 YAML spec 里**。

## 基本信息

- **一句话**：RFD4-Proteina flow-matching biomolecular design
- **执行方式**：容器（`rfd4`）
- **需要上游输入**：否（源 block）
- **容器入口**：`rfd4-generate`

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("rfd4", inputs="<输入路径>", <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--rfd4.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("rfd4", 参数名=值)` | 最常用 |

## 形状参数在哪

RFD4 的**长度、热点、埋藏全部在 `inputs` 指向的 YAML/JSON spec 里**，不在下面的 block 参数表里。

spec 顶层每个 key 是一套设计：

| spec 字段 | 类型 | 作用 |
|---|---|---|
| `input` | str | 条件化的 CIF。**必须 CIF**，PDB 会被拒绝 |
| `contig` | str | 新链段与保留段。**逗号分隔，`/0` 自己占一个 token** |
| `conditions` | dict | 条件字典：键是条件别名，值是选择器 |

`contig` 写法（`rfproteina/inference_utils/contig_spec.py:172` 按逗号切分）：

```yaml
# 单段靶点
contig: "60-90, /0, B1-114"
# 多段靶点，每段之间都要 /0
contig: "60-90, /0, B1-50, /0, C1-60"
```

常用 `conditions` 别名：

| 别名 | 作用 |
|---|---|
| `C_HOT` | 热点，binder 必须贴住的位点 |
| `C_SEQ` | 序列固定 / 重设计范围 |
| `C_CRDGRP` | 坐标组，保持刚性不动 |
| `C_RAS` | 按溶剂可及性分箱 |
| `C_SEC` | 二级结构条件化 |
| `C_HB` | 氢键 |
| `C_SALT` | 盐桥 |
| `C_HPHOB` | 疏水接触 |
| `C_PISTACK` / `C_PICATION` | π 堆积 / 阳离子-π |
| `C_MCOORD` | 金属配位 |
| `C_INTCRD` | 内部坐标 |
| `C_CENTROID` | 链质心 |
| `C_BP` / `C_NA_SS_STATE` | 碱基配对 / 核酸二级结构 |

选择器语法：

| 写法 | 含义 |
|---|---|
| `sel('B/*/[289]')` | B 链 289 号残基 |
| `sel('B/*/[195,197]')` | B 链 195 和 197 |
| `not sel('A')` | 排除 A 链 |
| `is_protein_backbone` | 所有蛋白骨架原子 |

**两个必须注意的坑**：

1. spec 里 `input` 的相对路径按 **spec 所在目录**解析，容器也只 bind 那一级目录 —— spec 和 CIF 必须放同一目录。
2. 靶点链若有残基缺口，必须先在输入 CIF 里拆成多条独立链，否则报 `bond_length ... 7.16 Å (limit 2.0 Å)`。

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `command_template` | `Optional[List[str]]` | `None` | — |
| `cloud` | `bool` | `false` | — |
| `ckpt_path` | `Optional[str]` | `None` | 模型包：HF 仓库 id，或含 config.json 与 model.safetensors 的本地目录。None 用 RFD4_WEIGHTS_DIR。 |
| `num_replicates` | `int` | `1` | 每个输入生成的设计数。 |
| `batch_size` | `int` | `1` | 采样器批大小（RFD4 配置键 ``batch_size``）。 |
| `seed` | `Optional[int]` | `None` | 基础种子；每个块按其下标偏移。 |
| `cyclic` | `bool` | `false` | Design a macrocyclic peptide binder. Rewrites each input into a conditioned CIF carrying a placeholder peptide chain and a closing _struct_conn record, then designs against it. |
| `peptide_length` | `int` | `12` | Residues in the cyclic peptide (used only when cyclic=True). |
| `peptide_chain` | `str` | `"A"` | Chain id for the designed peptide. Defaults to 'A' because downstream RFOptimization hard-requires the designed chain to be named A. A collision with a target chain is an error, not an auto-rename. |
| `target_chains` | `Optional[list[str]]` | `None` | Target chains to keep and condition on. None keeps every chain in the input. |
| `hotspots` | `Union[list[int \| str], dict[str, str], NoneType]` | `None` | Target atoms the peptide should contact (C_HOT). C_HOT is an atom-level condition, so naming the side-chain atoms is what pins the binder to the intended epitope; a bare residue number lets the model pick any atom of that residue. Accepts 40, 'D40', 'D40:NH1,NH2', or {'D40': 'NH1,NH2'}. |
| `cyclic_chemistry` | `str` | `"head_tail"` | Ring chemistry: 'head_tail' (N1-C12 amide, closes reliably), 'disulfide' (Cys SG-SG), or 'isopeptide' (Lys NZ-C). Head-to-tail is the only chemistry upstream measures at 100% closure. |
| `cyclic_motif_template` | `Optional[str]` | `None` | CIF holding a motif's measured coordinates, in the SAME frame as the input structure. The ring's first residues are pinned to those coordinates and identities (C_CRD + C_SEQ) instead of being designed. Requires cyclic_builder: the bundled builder leaves the whole ring to the model and ignores this field, so setting it alone is an error rather than a silent no-op. |
| `cyclic_motif_chain` | `str` | `"E"` | Chain id of the motif inside cyclic_motif_template. |
| `cyclic_motif_res_ids` | `Optional[list[int]]` | `None` | Residue ids of the motif in the template, in ring order. |
| `cyclic_builder` | `Optional[str]` | `None` | Path to an alternative cyclic-input builder supporting 'motif'. Defaults to the bundled build_cyclic_rfd4_input.py. |

## `extra_overrides`

原样传入的额外 Hydra 覆盖，如 ['recycle_strategy=high'] 或 ['length=120']。

| 项 | 作用 |
|---|---|
| `key=value` | 键已存在，直接覆盖 |
| `+key=value` | 键不存在，新增 |
| `++key=value` | 键存在但 struct 不允许覆盖，强制写 |

传的是**字符串列表**，每项原样拼进上游命令行：

```python
extra_overrides=["recycle_strategy=thinking_high", "++generation.args.nsteps=100"]
```

## 完整例子

### 最小 spec

```yaml
# design.yaml —— 必须和 target.cif 放在同一目录
my_design:
  input: target.cif
  contig: "60-90, /0, B1-114"
```

```python
h = engine.run("rfd4", inputs="design.yaml", num_replicates=2, seed=42)
```

### binder 设计：带热点、靶点序列冻结

```yaml
binder_design:
  input: target.cif
  contig: "60-90, /0, B147-362"
  conditions:
    C_HOT: {true: [{select: "sel('B/*/[195]') or sel('B/*/[197]')"}]}
    C_SEQ: {true: [{select: "not sel('A')"}]}
    C_CRDGRP: {1: [{select: "is_protein_backbone and not sel('A')"}]}
```

### 提高内部优化强度

```python
h = engine.run(
    "rfd4",
    inputs="design.yaml",
    num_replicates=2,
    extra_overrides=["recycle_strategy=thinking_high"],
)
```

**注意**：`recycle_strategy` 和 `args.nsteps` 不能同时改 —— thinking_high 的 schedule
写死 60 步，改 nsteps 会报 `recycle schedule expands to 60 steps; expected N`。

### 环肽（cyclic=True）

RFD4 **没有环化开关**，也**不需要环肽模板坐标**。环化靠输入结构里的一条
`_struct_conn` covale 记录；肽链本身是一串坐标全 0 的占位残基，序列和坐标都交给模型设计
（`C_SEQ = <M>`、不设 `C_CRD`）。`cyclic=True` 就是自动生成这种输入：

```python
h = engine.run(
    "rfd4",
    inputs="target.cif",
    cyclic=True,
    peptide_length=12,
    target_chains=["D", "E"],
    hotspots=[40, 45, 47, 86, 91, 95],
    num_replicates=8,
)
```

| 参数 | 默认 | 作用 |
|---|---|---|
| `cyclic` | False | 生成环肽输入再设计 |
| `peptide_length` | 12 | 环肽残基数 |
| `peptide_chain` | "A" | 肽链 id。默认 A，因为下游 RFOptimization 硬要求设计链叫 A；与靶点重名会直接报错 |
| `target_chains` | None | 保留哪些靶点链；None 保留全部 |
| `hotspots` | None | 靶点残基号，标成 `C_HOT` |
| `cyclic_chemistry` | "head_tail" | `head_tail` / `disulfide` / `isopeptide` |

**化学选 head_to_tail。** 官方 16 replicate 实测闭合率：head-to-tail 16/16，
disulfide 12/16，isopeptide 1/16（无输入坐标时）。本地 4 replicate 复现 head-to-tail 4/4。

环化是几何性质，不等于可设计性 —— 后面还要接 AF3/OpenFold3 回折并按
`iptm`/`plddt` 筛。判闭合要**双侧**：`|d - ideal| <= 0.3`，单向阈值会把
过冲（原子重叠）当成成功。

> 坑：`to_cif_file` 写不出这条闭合键。biotite 1.6.0 的 `_filter_canonical_links`
> 有运算符优先级 bug（`A & d == 1` 算成 `(A & d) == 1`），残基号差为奇数时恒为真，
> 环键被当普通肽键丢掉。block 里写完 CIF 后手工注入 `_struct_conn`。

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `inputs` | 你的脚本：`engine.run(..., inputs="路径")` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
