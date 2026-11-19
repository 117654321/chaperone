# contact_ms

## 干什么用的

计算 binder 和靶点之间的接触分子表面积（CMS）。

## 什么时候用它

量化界面接触面积，判断结合是否紧密。可限定只算某个表位。

## 基本信息

- **一句话**：Compute contact molecular surface between binder and target chains
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("contact_ms", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--contact_ms.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("contact_ms", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `binder_chains` | `List[str]` | **必填** | binder 的链 ID |
| `target_chains` | `List[str]` | **必填** | 靶点的链 ID |
| `target_atom_names` | `Optional[List[str]]` | `None` | 只对这些靶点原子名做 CMS 汇总（如 ['C12', 'O3']）。分子表面仍由完整靶点生成以保证遮挡关系正确，只是汇总范围受限。 |
| `target_residues` | `Optional[List[str]]` | `None` | 只对这些靶点残基做 CMS 汇总，用「链+编号」表示（如 ['B56', 'B121']）。用于表位导向设计——否则 binder 可能各项全局指标都达标却打偏了目标区域。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
