# rotamer_sweep

## 干什么用的

穷举指定侧链的 chi 角度组合。

## 什么时候用它

系统性扫描某个残基的构象空间。

## 基本信息

- **一句话**：Enumerate explicit functional side-chain chi combinations
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("rotamer_sweep", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--rotamer_sweep.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("rotamer_sweep", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `mutations` | `dict[str, str]` | **必填** | 要装入的残基身份，如 {'A12': 'PHE'}。 |
| `rotamers` | `dict[str, list[list[float]]]` | **必填** | 各位置的 chi 角度向量（度）。每个笛卡尔组合输出为独立结构。 |
| `max_combinations` | `int` | `1000` | 每个输入结构输出组合数的安全上限。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
