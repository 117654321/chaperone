# symmetry

## 干什么用的

算同源寡聚体组装相对循环点群的偏差。

## 什么时候用它

验证对称设计（C3 等）的对称性是否真的成立。

## 基本信息

- **一句话**：Cyclic point-group deviation of a homo-oligomeric assembly
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("symmetry", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--symmetry.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("symmetry", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `point_group` | `str` | `"C3"` | 期望的循环点群，如 'C3'。只支持 Cn；二面体群和多面体群需显式指定亚基归属。 |
| `chains` | `list[str] \| None` | `None` | 原聚体链 ID。默认按字母序取结构中所有蛋白链。要在大组装体中只评某个寡聚体时请显式指定。 |
| `backbone_only` | `bool` | `true` | 只用骨架 N/CA/C/O 做叠合。设 False 纳入侧链——仅在每个原聚体都完整打包时才可比。 |
| `exclude_hetero` | `bool` | `true` | 打分前丢弃 hetero（配体/辅因子）原子，避免结合的辅因子混入原聚体叠合。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
