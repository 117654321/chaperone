# rfd3

## 干什么用的

RFdiffusion3：通用扩散设计。支持单体、binder、酶、motif 支撑、对称、环化。

## 什么时候用它

主力骨架生成工具。**长度、环化、对称、热点都在 inputs 的 JSON 里**，不在 block 参数上。

## 基本信息

- **一句话**：RFdiffusion3 block
- **执行方式**：容器（`foundry`）
- **需要上游输入**：否（源 block）
- **容器入口**：`rfd3 design`

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("rfd3", inputs="<输入路径>", <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--rfd3.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("rfd3", 参数名=值)` | 最常用 |

## 形状参数在哪

RFD3 的**长度、环化、对称、热点全部在 `inputs` 指向的 JSON 里**，不在下面的 block 参数表里。

JSON 顶层每个 key 是一套独立设计，key 名必须匹配 `[A-Za-z0-9_-]`，不能带点号。

| JSON 字段 | 类型 | 作用 |
|---|---|---|
| `input` | str | 输入 PDB/CIF 路径 |
| `contig` | str | 设计链与保留段。`"50-80,/0,A1-100"` = 生成 50-80 残基新链 + 保留输入的 A1-100 |
| `length` | str | 长度约束，`'min-max'` 或单个整数 |
| `cyclic_chains` | list | **成环控制**，如 `["A"]` |
| `ligand` | str | 纳入的配体名，逗号分隔，如 `'HAX,OAA'` |
| `select_hotspots` | str | **热点**，如 `'B289'` 或 `'A56,A60-64'` |
| `select_fixed_atoms` | str | 固定坐标的原子选择 |
| `select_unfixed_sequence` | str | 放开序列的区段，如 `'A20-35'` |
| `select_buried` / `select_partially_buried` / `select_exposed` | str | 按 RASA 埋藏程度条件化 |
| `select_hbond_donor` / `select_hbond_acceptor` | str | 氢键供体/受体条件化 |
| `redesign_motif_sidechains` | bool | motif 侧链是否重设计 |
| `is_non_loopy` | bool | 偏好螺旋/片层，减少环区 |
| `plddt_enhanced` | bool | pLDDT 增强，默认 true |
| `partial_t` | float | 部分扩散的噪声强度（Å），≤15，None 关闭 |
| `symmetry` | dict | 对称设置，见下表 |
| `ori_token` | list | 原点坐标 `[x, y, z]` |
| `infer_ori_strategy` | str | 自动推断原点：`'com'` 或 `'hotspots'` |
| `unindex` | str | 取消索引的区段 |
| `dialect` | int | `1`=legacy，`2`=release（默认） |

`symmetry` 子字段：

| 子字段 | 类型 | 作用 |
|---|---|---|
| `id` | str | 对称群，如 `'C3'`、`'D2'`（只支持 C/D 型） |
| `is_unsym_motif` | str | 不参与对称化的组分，如 `'HEM'` 或 `'Y1-11,Z16-25'` |
| `is_symmetric_motif` | bool | true=输入 motif 已对称；false=按 ASU 处理并对称化 |

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

## 完整例子

### 只有 JSON，无条件生成

```json
{
  "monomer": {"contig": "100-100"}
}
```

```python
h = engine.run("rfd3", inputs="design.json", n_batches=4, batch_size=1)
```

### binder 设计：60-90 残基，环状，贴住 B289

```json
{
  "binder": {
    "input": "/abs/path/target.cif",
    "contig": "60-90,/0,B1-114",
    "cyclic_chains": ["A"],
    "select_hotspots": "B289",
    "is_non_loopy": true
  }
}
```

```python
h = engine.run("rfd3", inputs="binder.json", n_batches=4, batch_size=1, seed_offset=42)
```

### 不写文件，直接传 dict

```python
h = engine.run("rfd3", inputs={"binder": {"contig": "100-150"}})
```

### 对称设计：C3 三聚体

```json
{
  "trimer": {
    "contig": "80-80",
    "symmetry": {"id": "C3"}
  }
}
```

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `inputs` | 你的脚本：`engine.run(..., inputs="路径")` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
