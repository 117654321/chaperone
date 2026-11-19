# plip

## 干什么用的

用 PLIP 分析蛋白-配体相互作用类型（氢键、疏水、π 堆积等）。

## 什么时候用它

要看结合模式的细节，不只是总分。

## 基本信息

- **一句话**：Profile protein-ligand interactions using PLIP
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("plip", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--plip.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("plip", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `ligand_ids` | `Optional[list[str]]` | `None` | 按 PLIP ID 过滤特定结合位点（格式 'HetID:Chain:Position'，如 'LIG:A:301'）。None 时分析所有检测到的配体。 |
| `per_residue` | `bool` | `false` | 包含逐残基的相互作用总数（如 per_res.A42 = 3）。 |
| `include_details` | `bool` | `false` | 存在多个结合位点时包含逐配体的相互作用分解。 |
| `verbose` | `bool` | `false` | True 时输出还包含 `per_interaction_details`：对每类相互作用给出原子级信息 dict 列表（ligand_atom、protein_atom、residue、distance 等）。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
