# dssr_motif_base_pairing

## 干什么用的

用 DSSR 检查 motif 碱基配对，看原生分类是否保留。

## 什么时候用它

RNA/DNA 设计的 motif 完整性验证。

## 基本信息

- **一句话**：Mapped motif base pairing and native DSSR classification retention.
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("dssr_motif_base_pairing", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--dssr_motif_base_pairing.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("dssr_motif_base_pairing", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `x3dna_dssr_bin` | `str \| None` | _运行时计算_ | x3dna-dssr 的路径。默认 $X3DNA_BIN_DIR/x3dna-dssr。 |
| `x3dna_home` | `str \| None` | _运行时计算_ | 调用 x3dna-dssr 时导出的 $X3DNA 值。 |
| `reference` | `str` | **必填** | 用于推导配对注释的天然 RNA/DNA 结构。 |
| `residues` | `list[str]` | **必填** | 要报告的参考 motif 残基 id，如 ['A10', 'B4']。 |
| `continue_on_error` | `bool` | `false` | 预测结构 DSSR 处理失败时返回逐行状态/错误诊断，而不是中止整个指标 block。参考结构配置错误仍然致命。 |
| `which` | `list[int]` | `[0, -1]` | 携带 diffused_index_map 和预测坐标的结构。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
