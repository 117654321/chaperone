# rotamer_metrics

## 干什么用的

算蛋白侧链的 rotamer 质量（要 Dunbrack 库）。

## 什么时候用它

评估侧链打包质量，看有没有不合理的构象。

## 基本信息

- **一句话**：Compute rotamer quality metrics for protein sidechains
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("rotamer_metrics", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--rotamer_metrics.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("rotamer_metrics", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `backend` | `Literal['dunbrack', 'peppr']` | `"dunbrack"` | 打分后端：'peppr'（经 peppr 使用 Top8000 库）或 'dunbrack'（骨架依赖的 Dunbrack 库）。 |
| `motif_only` | `bool` | `true` | 只对标注为 motif 的残基打分（is_motif_atom）。结构没有 motif 注释时对所有残基打分。 |
| `include_rama` | `bool` | `true` | 同时计算 Ramachandran 分数（仅 peppr 后端）。 |
| `detailed_output` | `bool` | `false` | 包含按残基类型分解的分数。 |
| `per_residue_output` | `bool` | `true` | 用 diffused_index_map 元数据映射回原始残基标识，输出逐原始残基的分数（如 mean_rotamer_pct.A1）。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
