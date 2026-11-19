"""为每个 block 生成一份 Markdown 参数文档，放在 docs/params/ 下。

面向「查阅」，不是「当配置文件用」：一个工具一个 .md。

每个文件包含：

- **干什么用的 / 什么时候用它** —— 来自 configs/block_purpose_zh.json
- **怎么调用** —— 三种传参方式对比
- **形状参数在哪** —— 骨架类工具的长度/环化/对称/热点实际写在 JSON/spec 里
- **全部参数表** —— 参数名、类型、默认值、中文说明
- **特殊字段** —— extra_overrides / args / filters 怎么传
- **完整例子** —— 可直接复制的代码

用法：

    python scripts/export_param_docs.py               # 全部
    python scripts/export_param_docs.py --blocks rfd3 rfd4
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import typing
import types
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "docs" / "params"
ZH_FILE = REPO / "configs" / "block_params_zh.json"
PURPOSE_FILE = REPO / "configs" / "block_purpose_zh.json"

# 这些字段由脚本运行时提供或另有专门讲法，不在参数表里重复
_RUNTIME = {"name", "inputs", "data", "source"}
_SPECIAL = {
    "extra_overrides",
    "args",
    "filters",
    "filter_overrides",
    "advanced_overrides",
    "overrides",
}

_zh: dict[str, str] | None = None
_PURPOSE: dict[str, dict] = {}
if PURPOSE_FILE.is_file():
    _PURPOSE = json.loads(PURPOSE_FILE.read_text())


def zh(text: str) -> str:
    global _zh
    if _zh is None:
        _zh = json.loads(ZH_FILE.read_text()) if ZH_FILE.is_file() else {}
    flat = re.sub(r"\s+", " ", (text or "").strip())
    return _zh.get(flat, flat)


def type_text(ann) -> str:
    t = str(ann).replace("typing.", "").replace("chaperone.", "")
    return re.sub(r"<class '([^']+)'>", r"\1", t)


def _repo_relative(value: str) -> str:
    """把仓库内的绝对路径换成 ``<repo>/...``，其余原样返回。

    默认值里的脚本路径由 ``Path(__file__)`` 推导，导出时已经是绝对路径。写进
    文档会把某台机器的目录布局固化下来，换一台机器读起来就是错的。
    """
    if not value.startswith("/"):
        return value
    repo_root = Path(__file__).resolve().parents[1]
    try:
        return f"<repo>/{Path(value).resolve().relative_to(repo_root).as_posix()}"
    except (OSError, ValueError):
        return value


def default_text(field) -> str:
    from pydantic_core import PydanticUndefined

    if field.default is PydanticUndefined:
        return "**必填**" if field.default_factory is None else "_运行时计算_"
    v = field.default
    if v is None:
        return "`None`"
    if isinstance(v, bool):
        return "`true`" if v else "`false`"
    if isinstance(v, (int, float)):
        return f"`{v}`"
    if isinstance(v, str):
        v = _repo_relative(v)
        return f'`"{v}"`' if v else '`""`'
    if isinstance(v, (list, tuple)):
        return "`[]`" if not v else f"`{list(v)}`"
    if isinstance(v, dict):
        return "`{}`" if not v else f"`{v}`"
    return f"`{v}`"


def esc(s: str) -> str:
    """转义表格里的竖线和换行。

    已经带反斜杠的竖线（``\\|``）不再重复转义，否则渲染出来是两层反斜杠。
    """
    text = (s or "").replace("\n", " ")
    # 先保护已有的 \| ，转义裸 | ，再还原
    text = text.replace("\\|", "\x00")
    text = text.replace("|", "\\|")
    return text.replace("\x00", "\\|").strip()


def _render_entrypoint(command: list[str]) -> str:
    """入口命令，把仓库内脚本路径改成 ``<repo>/...``。

    ``_script_spec.command`` 里的脚本路径由 ``Path(__file__)`` 推导，导出时已经
    是绝对路径。写进文档会把某台机器的目录布局固化下来，换一台机器读起来就是
    错的；仓库内路径用占位符，其余（``python``、容器内路径）原样保留。
    """
    repo_root = Path(__file__).resolve().parents[1]
    rendered = []
    for part in command:
        # Only rewrite arguments that already name a real path inside the repo.
        # A bare command ("python") or a flag ("--db_dir=/databases") must pass
        # through untouched, so require an existing absolute path first.
        candidate = Path(part)
        if not candidate.is_absolute():
            rendered.append(part)
            continue
        try:
            resolved = candidate.resolve()
            rendered.append(f"<repo>/{resolved.relative_to(repo_root).as_posix()}")
        except (OSError, ValueError):
            rendered.append(part)
    return " ".join(rendered)


def param_table(fields: dict) -> list[str]:
    L = ["| 参数 | 类型 | 默认值 | 说明 |", "|---|---|---|---|"]
    for fn, f in fields.items():
        L.append(
            f"| `{fn}` | `{esc(type_text(f.annotation))[:60]}` | "
            f"{default_text(f)} | {esc(zh(f.description or '')) or '—'} |"
        )
    return L


# ── 每个工具的形状参数说明（读源码得到，不是抄文档）──────────────────
_SHAPE: dict[str, list[str]] = {
    "rfd3": [
        "RFD3 的**长度、环化、对称、热点全部在 `inputs` 指向的 JSON 里**，不在下面的 block 参数表里。",
        "",
        "JSON 顶层每个 key 是一套独立设计，key 名必须匹配 `[A-Za-z0-9_-]`，不能带点号。",
        "",
        "| JSON 字段 | 类型 | 作用 |",
        "|---|---|---|",
        "| `input` | str | 输入 PDB/CIF 路径 |",
        "| `contig` | str | 设计链与保留段。`\"50-80,/0,A1-100\"` = 生成 50-80 残基新链 + 保留输入的 A1-100 |",
        "| `length` | str | 长度约束，`'min-max'` 或单个整数 |",
        "| `cyclic_chains` | list | **成环控制**，如 `[\"A\"]` |",
        "| `ligand` | str | 纳入的配体名，逗号分隔，如 `'HAX,OAA'` |",
        "| `select_hotspots` | str | **热点**，如 `'B289'` 或 `'A56,A60-64'` |",
        "| `select_fixed_atoms` | str | 固定坐标的原子选择 |",
        "| `select_unfixed_sequence` | str | 放开序列的区段，如 `'A20-35'` |",
        "| `select_buried` / `select_partially_buried` / `select_exposed` | str | 按 RASA 埋藏程度条件化 |",
        "| `select_hbond_donor` / `select_hbond_acceptor` | str | 氢键供体/受体条件化 |",
        "| `redesign_motif_sidechains` | bool | motif 侧链是否重设计 |",
        "| `is_non_loopy` | bool | 偏好螺旋/片层，减少环区 |",
        "| `plddt_enhanced` | bool | pLDDT 增强，默认 true |",
        "| `partial_t` | float | 部分扩散的噪声强度（Å），≤15，None 关闭 |",
        "| `symmetry` | dict | 对称设置，见下表 |",
        "| `ori_token` | list | 原点坐标 `[x, y, z]` |",
        "| `infer_ori_strategy` | str | 自动推断原点：`'com'` 或 `'hotspots'` |",
        "| `unindex` | str | 取消索引的区段 |",
        "| `dialect` | int | `1`=legacy，`2`=release（默认） |",
        "",
        "`symmetry` 子字段：",
        "",
        "| 子字段 | 类型 | 作用 |",
        "|---|---|---|",
        "| `id` | str | 对称群，如 `'C3'`、`'D2'`（只支持 C/D 型） |",
        "| `is_unsym_motif` | str | 不参与对称化的组分，如 `'HEM'` 或 `'Y1-11,Z16-25'` |",
        "| `is_symmetric_motif` | bool | true=输入 motif 已对称；false=按 ASU 处理并对称化 |",
    ],
    "rfd3na": [
        "与 rfd3 同一套 JSON 结构，额外支持核酸。",
        "",
        "`contig` 里核酸链加后缀：`A1-30:dna`（DNA）、`B1-40:rna`（RNA）。`cyclic_chains` 同样可用。",
    ],
    "rfd3_partial": [
        "与 rfd3 同一套 JSON 结构。",
        "",
        "主开关是 `partial_t`：噪声强度（Å），越大偏离输入越远，推荐 ≤15。`None` 表示不启用部分扩散，退化成普通生成。",
    ],
    "rfd4": [
        "RFD4 的**长度、热点、埋藏全部在 `inputs` 指向的 YAML/JSON spec 里**，不在下面的 block 参数表里。",
        "",
        "spec 顶层每个 key 是一套设计：",
        "",
        "| spec 字段 | 类型 | 作用 |",
        "|---|---|---|",
        "| `input` | str | 条件化的 CIF。**必须 CIF**，PDB 会被拒绝 |",
        "| `contig` | str | 新链段与保留段。**逗号分隔，`/0` 自己占一个 token** |",
        "| `conditions` | dict | 条件字典：键是条件别名，值是选择器 |",
        "",
        "`contig` 写法（`rfproteina/inference_utils/contig_spec.py:172` 按逗号切分）：",
        "",
        "```yaml",
        "# 单段靶点",
        'contig: "60-90, /0, B1-114"',
        "# 多段靶点，每段之间都要 /0",
        'contig: "60-90, /0, B1-50, /0, C1-60"',
        "```",
        "",
        "常用 `conditions` 别名：",
        "",
        "| 别名 | 作用 |",
        "|---|---|",
        "| `C_HOT` | 热点，binder 必须贴住的位点 |",
        "| `C_SEQ` | 序列固定 / 重设计范围 |",
        "| `C_CRDGRP` | 坐标组，保持刚性不动 |",
        "| `C_RAS` | 按溶剂可及性分箱 |",
        "| `C_SEC` | 二级结构条件化 |",
        "| `C_HB` | 氢键 |",
        "| `C_SALT` | 盐桥 |",
        "| `C_HPHOB` | 疏水接触 |",
        "| `C_PISTACK` / `C_PICATION` | π 堆积 / 阳离子-π |",
        "| `C_MCOORD` | 金属配位 |",
        "| `C_INTCRD` | 内部坐标 |",
        "| `C_CENTROID` | 链质心 |",
        "| `C_BP` / `C_NA_SS_STATE` | 碱基配对 / 核酸二级结构 |",
        "",
        "选择器语法：",
        "",
        "| 写法 | 含义 |",
        "|---|---|",
        "| `sel('B/*/[289]')` | B 链 289 号残基 |",
        "| `sel('B/*/[195,197]')` | B 链 195 和 197 |",
        "| `not sel('A')` | 排除 A 链 |",
        "| `is_protein_backbone` | 所有蛋白骨架原子 |",
        "",
        "**两个必须注意的坑**：",
        "",
        "1. spec 里 `input` 的相对路径按 **spec 所在目录**解析，容器也只 bind 那一级目录 —— spec 和 CIF 必须放同一目录。",
        "2. 靶点链若有残基缺口，必须先在输入 CIF 里拆成多条独立链，否则报 `bond_length ... 7.16 Å (limit 2.0 Å)`。",
    ],
    "rfd1": [
        "RFD1 的形状参数**就是 block 字段**，不在 JSON 里：",
        "",
        "| 参数 | 作用 |",
        "|---|---|",
        "| `contigs` | 长度与结构。`'150-150'` 无条件；`'5-15/A10-25/30-40'` 骨架支撑；`'A1-7/150/0 B1-7/150/0'` 多聚体 |",
        "| `num_designs` | 每个 chunk 生成几个 |",
        "| `symmetry` | `'c3'` / `'c5'` / `'d3'` / `'tetrahedral'`，会自动切到 symmetry 配置 |",
        "| `input_pdb` | motif 支撑或 binder 设计的目标 PDB |",
        "| `hotspot_residues` | 热点，如 `['A30','A33']` |",
        "| `inpaint_seq` / `inpaint_str` | inpaint 的序列 / 结构位置 |",
        "| `denoiser.noise_scale_ca` / `noise_scale_frame` | 平移 / 旋转噪声缩放 |",
        "| `diffuser.T` | 去噪步数 |",
        "",
        "环化：RFD1 没有独立的环化字段，通过 `contigs` 的对称表达实现。",
    ],
    "rfd2": [
        "RFD2 的形状参数分两处：",
        "",
        "block 字段：`inputs`（YAML 路径）、`num_designs`、`ckpt_path`、`raise_on_missing_trbs`。",
        "",
        "`inputs` 指向的 YAML 常用键（Hydra 风格）：",
        "",
        "| 键 | 作用 |",
        "|---|---|",
        "| `contigs` | 如 `['100']` |",
        "| `diffuser.T` | 去噪步数 |",
        "| `inference.input_pdb` | 必须**绝对路径** |",
        "| `recenter` | 依赖输入里的 ORI 残基定中心 |",
        "",
        "**注意**：输入 PDB 必须带 `ORI` HETATM，否则 recenter 报错。",
    ],
}


# ── 完整例子 ────────────────────────────────────────────────────────
_EXAMPLES: dict[str, list[str]] = {
    "rfd3": [
        "### 只有 JSON，无条件生成",
        "",
        "```json",
        "{",
        '  "monomer": {"contig": "100-100"}',
        "}",
        "```",
        "",
        "```python",
        'h = engine.run("rfd3", inputs="design.json", n_batches=4, batch_size=1)',
        "```",
        "",
        "### binder 设计：60-90 残基，环状，贴住 B289",
        "",
        "```json",
        "{",
        '  "binder": {',
        '    "input": "/abs/path/target.cif",',
        '    "contig": "60-90,/0,B1-114",',
        '    "cyclic_chains": ["A"],',
        '    "select_hotspots": "B289",',
        '    "is_non_loopy": true',
        "  }",
        "}",
        "```",
        "",
        "```python",
        'h = engine.run("rfd3", inputs="binder.json", n_batches=4, batch_size=1, seed_offset=42)',
        "```",
        "",
        "### 不写文件，直接传 dict",
        "",
        "```python",
        'h = engine.run("rfd3", inputs={"binder": {"contig": "100-150"}})',
        "```",
        "",
        "### 对称设计：C3 三聚体",
        "",
        "```json",
        "{",
        '  "trimer": {',
        '    "contig": "80-80",',
        '    "symmetry": {"id": "C3"}',
        "  }",
        "}",
        "```",
    ],
    "rfd4": [
        "### 最小 spec",
        "",
        "```yaml",
        "# design.yaml —— 必须和 target.cif 放在同一目录",
        "my_design:",
        "  input: target.cif",
        '  contig: "60-90, /0, B1-114"',
        "```",
        "",
        "```python",
        'h = engine.run("rfd4", inputs="design.yaml", num_replicates=2, seed=42)',
        "```",
        "",
        "### binder 设计：带热点、靶点序列冻结",
        "",
        "```yaml",
        "binder_design:",
        "  input: target.cif",
        '  contig: "60-90, /0, B147-362"',
        "  conditions:",
        '    C_HOT: {true: [{select: "sel(\'B/*/[195]\') or sel(\'B/*/[197]\')"}]}',
        '    C_SEQ: {true: [{select: "not sel(\'A\')"}]}',
        '    C_CRDGRP: {1: [{select: "is_protein_backbone and not sel(\'A\')"}]}',
        "```",
        "",
        "### 提高内部优化强度",
        "",
        "```python",
        "h = engine.run(",
        '    "rfd4",',
        '    inputs="design.yaml",',
        "    num_replicates=2,",
        '    extra_overrides=["recycle_strategy=thinking_high"],',
        ")",
        "```",
        "",
        "**注意**：`recycle_strategy` 和 `args.nsteps` 不能同时改 —— thinking_high 的 schedule",
        "写死 60 步，改 nsteps 会报 `recycle schedule expands to 60 steps; expected N`。",
        "",
        "### 环肽（cyclic=True）",
        "",
        "RFD4 **没有环化开关**，也**不需要环肽模板坐标**。环化靠输入结构里的一条",
        "`_struct_conn` covale 记录；肽链本身是一串坐标全 0 的占位残基，序列和坐标都交给模型设计",
        "（`C_SEQ = <M>`、不设 `C_CRD`）。`cyclic=True` 就是自动生成这种输入：",
        "",
        "```python",
        "h = engine.run(",
        '    "rfd4",',
        '    inputs="target.cif",',
        "    cyclic=True,",
        "    peptide_length=12,",
        '    target_chains=["D", "E"],',
        "    hotspots=[40, 45, 47, 86, 91, 95],",
        "    num_replicates=8,",
        ")",
        "```",
        "",
        "| 参数 | 默认 | 作用 |",
        "|---|---|---|",
        '| `cyclic` | False | 生成环肽输入再设计 |',
        '| `peptide_length` | 12 | 环肽残基数 |',
        '| `peptide_chain` | "A" | 肽链 id。默认 A，因为下游 RFOptimization 硬要求设计链叫 A；与靶点重名会直接报错 |',
        '| `target_chains` | None | 保留哪些靶点链；None 保留全部 |',
        '| `hotspots` | None | 靶点残基号，标成 `C_HOT` |',
        '| `cyclic_chemistry` | "head_tail" | `head_tail` / `disulfide` / `isopeptide` |',
        "",
        "**化学选 head_to_tail。** 官方 16 replicate 实测闭合率：head-to-tail 16/16，",
        "disulfide 12/16，isopeptide 1/16（无输入坐标时）。本地 4 replicate 复现 head-to-tail 4/4。",
        "",
        "环化是几何性质，不等于可设计性 —— 后面还要接 AF3/OpenFold3 回折并按",
        "`iptm`/`plddt` 筛。判闭合要**双侧**：`|d - ideal| <= 0.3`，单向阈值会把",
        "过冲（原子重叠）当成成功。",
        "",
        "> 坑：`to_cif_file` 写不出这条闭合键。biotite 1.6.0 的 `_filter_canonical_links`",
        "> 有运算符优先级 bug（`A & d == 1` 算成 `(A & d) == 1`），残基号差为奇数时恒为真，",
        "> 环键被当普通肽键丢掉。block 里写完 CIF 后手工注入 `_struct_conn`。",
    ],
    "rfd1": [
        "### 无条件单体",
        "",
        "```python",
        'engine.run("rfd1", contigs="150-150", num_designs=4, diffuser_T=50)',
        "```",
        "",
        "### C3 对称",
        "",
        "```python",
        'engine.run("rfd1", contigs="80-80", symmetry="c3", num_designs=2)',
        "```",
        "",
        "### motif 支撑",
        "",
        "```python",
        'engine.run("rfd1", contigs="5-15/A10-25/30-40", input_pdb="motif.pdb", num_designs=2)',
        "```",
        "",
        "### binder 设计",
        "",
        "```python",
        'engine.run("rfd1", contigs="100-100,/0,B1-114", hotspot_residues=["B50"], num_designs=4)',
        "```",
    ],
    "rfd2": [
        "```yaml",
        "# chantest.yaml",
        "contigs: ['100']",
        "diffuser:",
        "  T: 50",
        "inference:",
        "  input_pdb: /abs/path/motif_ORI.pdb   # 绝对路径 + 必须带 ORI 残基",
        "```",
        "",
        "```python",
        'engine.run("rfd2", inputs="chantest.yaml", num_designs=1)',
        "```",
    ],
}

# 有特殊传参方式的 block，单独说明
_SPECIAL_DOCS: dict[str, list[str]] = {
    "extra_overrides": [
        "| 项 | 作用 |",
        "|---|---|",
        "| `key=value` | 键已存在，直接覆盖 |",
        "| `+key=value` | 键不存在，新增 |",
        "| `++key=value` | 键存在但 struct 不允许覆盖，强制写 |",
        "",
        "传的是**字符串列表**，每项原样拼进上游命令行：",
        "",
        "```python",
        'extra_overrides=["recycle_strategy=thinking_high", "++generation.args.nsteps=100"]',
        "```",
    ],
    "args": [
        "嵌套的 CLI 参数字典，传给上游工具（LigandMPNN / ProteinMPNN 自身）：",
        "",
        "```python",
        'args={"number_of_packs_per_design": 1, "temperature": 0.1}',
        "```",
        "",
        "**坑**：`temperature` 这类参数在 `args` 里，不在 block 顶层。",
        "写到顶层会因 `extra_forbidden` 报错（这个 block 显式禁止了额外字段）。",
    ],
    "filters": [
        "指标阈值，值是 `MetricFilter` 对象。YAML 里用简写，Python 里直接构造：",
        "",
        "```python",
        "from blocks.util_blocks.filter import MetricFilter",
        "",
        "Filter(filters={",
        '    "af3.plddt": MetricFilter(min=70.0),',
        '    "af3.min_pae_interaction": MetricFilter(max=2.0),',
        '    "mpnn.overall_confidence": MetricFilter(',
        '        quantile=0.125, quantile_direction="higher", parent_based=True),',
        "})",
        "```",
        "",
        "| 字段 | 作用 |",
        "|---|---|",
        "| `min` / `max` | 阈值上下界 |",
        "| `quantile` | 取分位，如 0.25 = 前 25% |",
        "| `quantile_direction` | `higher` = 值越大越好 |",
        "| `parent_based` | true = 每个上游设计各取最优（不是全局排序） |",
    ],
}

# 总览分组
_GROUPS = [
    ("骨架生成", ["rfd1", "rfd2", "rfd3", "rfd3na", "rfd3_partial", "rfd4"]),
    ("端到端设计", ["bindcraft", "bindcraft2", "protein_hunter", "boltzgen",
                    "disco", "proteina_complexa", "rfoptimization"]),
    ("序列设计", ["mpnn", "foundry_mpnn", "esm2", "e1"]),
    ("结构预测", ["af3", "af3_with_target_template", "boltz2", "boltz2_steered",
                  "chai1", "colabfold", "esmfold2", "openfold3", "protenix",
                  "rf3", "simplefold"]),
    ("打分与筛选", ["filter", "ipsae", "mpnn_score", "peppr", "rmsd", "tm_score",
                    "tm_score_rna", "ppi_ddg", "ligand_ddg", "ligand_ddg_soft",
                    "tmol_interface", "tmol_minimize"]),
    ("结构与注释", ["to_cif", "to_pdb", "transform", "annotate", "copy",
                    "select_chains", "restore_sidechains", "materialize"]),
]


def render(name: str) -> str:
    from blocks import Blocks

    cls = Blocks[name]
    fields = cls.model_fields

    container = ""
    try:
        spec = getattr(cls, "_script_spec", None)
        img = getattr(spec, "image", None) if spec else None
        container = getattr(img, "name", "") or ""
    except Exception:
        pass

    mode = "容器" if container else "纯 Python"
    L: list[str] = []
    L.append(f"# {name}")
    L.append("")

    purpose = _PURPOSE.get(name)
    if purpose:
        L.append("## 干什么用的")
        L.append("")
        L.append(purpose.get("what", ""))
        L.append("")
        if purpose.get("when"):
            L.append("## 什么时候用它")
            L.append("")
            L.append(purpose["when"])
            L.append("")

    L.append("## 基本信息")
    L.append("")
    L.append(f"- **一句话**：{getattr(cls, '_description', '') or '—'}")
    L.append(f"- **执行方式**：{mode}" + (f"（`{container}`）" if container else ""))
    L.append(
        f"- **需要上游输入**："
        f"{'是' if getattr(cls, '_requires_input', False) else '否（源 block）'}"
    )
    if getattr(cls, "_script_spec", None):
        L.append(f"- **容器入口**：`{_render_entrypoint(cls._script_spec.command)}`")
    L.append("")

    # 调用方式
    L.append("## 怎么调用")
    L.append("")
    L.append("```python")
    L.append("from chaperone import ExecutionEngine, init_cli")
    L.append("init_cli()")
    L.append('engine = ExecutionEngine(rundir="out")')
    if getattr(cls, "_requires_input", False):
        L.append(f'h = engine.run("{name}", data=upstream_handler, <参数>=<值>)')
    else:
        L.append(f'h = engine.run("{name}", inputs="<输入路径>", <参数>=<值>)')
    L.append("```")
    L.append("")
    L.append("参数三种传法，优先级从高到低：")
    L.append("")
    L.append("| 方式 | 写法 | 用途 |")
    L.append("|---|---|---|")
    L.append(f"| 命令行 | `--{name}.参数名=值` | 临时试，不改代码 |")
    L.append("| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |")
    L.append(f'| 脚本 kwargs | `engine.run("{name}", 参数名=值)` | 最常用 |')
    L.append("")

    # 形状参数
    if name in _SHAPE:
        L.append("## 形状参数在哪")
        L.append("")
        L.extend(_SHAPE[name])
        L.append("")

    # 参数表
    normal = {
        fn: f
        for fn, f in fields.items()
        if fn not in _RUNTIME and fn not in _SPECIAL
    }
    if normal:
        L.append("## 全部参数")
        L.append("")
        L.extend(param_table(normal))
        L.append("")

    # 特殊字段
    for fname in ("extra_overrides", "args", "filters", "filter_overrides",
                  "advanced_overrides", "overrides"):
        if fname not in fields:
            continue
        L.append(f"## `{fname}`")
        L.append("")
        f = fields[fname]
        if f.description:
            L.append(zh(f.description))
            L.append("")
        if fname == "args":
            nested = getattr(f.annotation, "model_fields", None)
            if nested:
                L.append("可设的子参数：")
                L.append("")
                L.extend(param_table(dict(nested.items())))
                L.append("")
        L.extend(
            _SPECIAL_DOCS.get(
                fname, ["这是上游设置的浅层覆盖字典，整体替换而不是逐项合并。"]
            )
        )
        L.append("")

    # 例子
    if name in _EXAMPLES:
        L.append("## 完整例子")
        L.append("")
        L.extend(_EXAMPLES[name])
        L.append("")

    # 运行时参数
    L.append("## 由脚本提供的参数")
    L.append("")
    L.append("这些不写进参数表，运行时由引擎或你的脚本传入：")
    L.append("")
    L.append("| 参数 | 谁提供 |")
    L.append("|---|---|")
    if "inputs" in fields:
        L.append("| `inputs` | 你的脚本：`engine.run(..., inputs=\"路径\")` |")
    if "data" in fields or getattr(cls, "_requires_input", False):
        L.append("| `data` | 引擎：`engine.run(..., data=上游handler)` |")
    L.append("| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |")
    L.append("")

    return "\n".join(L)


def render_index() -> str:
    idx = [
        "# Chaperone block 总览",
        "",
        f"{len(_PURPOSE)} 个 block 的中文说明。每个文件里还有完整参数表、调用方式和例子。",
        "",
        "重新生成：`python scripts/export_param_docs.py`",
        "",
    ]
    covered = set()
    for title, names in _GROUPS:
        rows = [n for n in names if n in _PURPOSE]
        if not rows:
            continue
        idx.append(f"## {title}")
        idx.append("")
        idx.append("| block | 干什么 |")
        idx.append("|---|---|")
        for n in rows:
            covered.add(n)
            idx.append(f"| [`{n}`]({n}.md) | {_PURPOSE[n]['what'].split('。')[0]} |")
        idx.append("")

    rest = sorted(set(_PURPOSE) - covered)
    if rest:
        idx.append("## 其他")
        idx.append("")
        idx.append("| block | 干什么 |")
        idx.append("|---|---|")
        for n in rest:
            idx.append(f"| [`{n}`]({n}.md) | {_PURPOSE[n]['what'].split('。')[0]} |")
        idx.append("")
    return "\n".join(idx)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocks", nargs="*", default=None)
    parser.add_argument("--out", default=str(OUT_DIR))
    args = parser.parse_args()

    from blocks import Blocks

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    names = args.blocks or sorted(Blocks.keys())
    written = 0
    for name in names:
        try:
            (out / f"{name}.md").write_text(render(name))
            written += 1
        except Exception as exc:
            print(f"  SKIP {name}: {exc}")

    if not args.blocks:
        (out / "README.md").write_text(render_index())
        print(f"写入 {written} 个文档 + README.md 总览到 {out}")
    else:
        print(f"写入 {written} 个文档到 {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
