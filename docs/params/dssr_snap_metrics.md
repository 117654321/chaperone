# dssr_snap_metrics

## 干什么用的

用 x3dna-dssr 和 x3dna-snap 算蛋白-DNA 复合物的生物物理指标。

## 什么时候用它

核酸复合物的深度几何分析。

## 基本信息

- **一句话**：Per-design biophysical metrics for protein-DNA complexes via x3dna-dssr and x3dna-snap (3DNA v2.3).
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("dssr_snap_metrics", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--dssr_snap_metrics.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("dssr_snap_metrics", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `x3dna_dssr_bin` | `str \| None` | _运行时计算_ | x3dna-dssr 可执行文件路径。默认取环境变量 ``$X3DNA_BIN_DIR/x3dna-dssr``（在 .env.local 里配置）。 |
| `x3dna_snap_bin` | `str \| None` | _运行时计算_ | x3dna-snap 可执行文件路径。默认取环境变量 ``$X3DNA_BIN_DIR/x3dna-snap``。 |
| `x3dna_home` | `str \| None` | _运行时计算_ | 调用这两个可执行文件时导出的 $X3DNA 值（3DNA 安装根目录，含 config/、lib/ 等）。默认取 ``X3DNA_DIR`` 设置。 |
| `skip_snap` | `bool` | `false` | True 时完全跳过 SNAP（快路径）——SNAP 相关指标为 NaN。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
