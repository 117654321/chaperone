# reference_motif_rmsd

## 干什么用的

按 diffused_index_map 算 motif 相对输入的 RMSD。

## 什么时候用它

验证设计的 motif 有没有跑位。

## 基本信息

- **一句话**：Motif RMSD against the input reference, via diffused_index_map
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("reference_motif_rmsd", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--reference_motif_rmsd.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("reference_motif_rmsd", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `reference` | `str` | **必填** | motif 来源的规范结构路径。 |
| `which` | `List[int]` | `[0, -1]` | 每行 structures 列表中的两个下标：携带 diffused_index_map 的结构，以及要打分的结构。默认 [0, -1] 表示从扩散结构读映射、对最终预测打分。 |
| `residues` | `Optional[List[str]]` | `None` | 要打分的参考残基 id，如 ['A10-12', 'B4']。默认取 diffused_index_map 中的全部条目。 |
| `ligands` | `List[str]` | _运行时计算_ | 要纳入的配体/离子残基名，如 ['MN']。RFD3NA 不把非聚合物组分放进 diffused_index_map，因此按残基名在两个结构中匹配。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
