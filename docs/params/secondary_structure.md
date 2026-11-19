# secondary_structure

## 干什么用的

算二级结构组成，以及配体周围口袋的 loop / pLDDT 无序度。

## 什么时候用它

评估设计的二级结构合理性，或看结合口袋的柔性。

## 基本信息

- **一句话**：Per-fold SS composition + loop/pLDDT disorder, globally and pocket-around-ligand
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("secondary_structure", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--secondary_structure.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("secondary_structure", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `pocket_cutoff` | `float` | `8.0` | 判定残基属于口袋的 Å 截断（任一非氢蛋白原子距任一配体原子在此距离内）。 |
| `plddt_threshold` | `float` | `70.0` | 逐残基平均 b_factor 低于此值即视为低置信（按 pLDDT 语义；AF3/Boltz/RF3 的 CIF 中 b_factor 承载 0-100 的 pLDDT）。 |
| `plddt_min_signal` | `float` | `50.0` | b_factor → pLDDT（0-100）的自动缩放规则：- max(bf) ≤ 1.5 → 认定为 0-1 尺度（RF3），乘以 100；- max(bf) ≥ plddt_min_signal → 认定为 0-100 尺度（AF3/Boltz）。 |
| `verbose` | `bool` | `false` | True 时额外输出 `ss_string`、片段拓扑，以及逐残基的 `residue_records` 列表（含 residue_id、resname、ss、plddt、in_pocket）。 |
| `chains` | `Optional[List[str]]` | `None` | 只对这些链 ID 计算二级结构（如 ['B']）。None 时包含全部链。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
