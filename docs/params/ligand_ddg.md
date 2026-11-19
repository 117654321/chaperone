# ligand_ddg

## 干什么用的

Rosetta DDG 计算蛋白-配体结合能。

## 什么时候用它

需要物理层面的结合能，不只看预测器置信度。需要 DAlphaBall。

## 基本信息

- **一句话**：Compute Rosetta DDG binding energy
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("ligand_ddg", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--ligand_ddg.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("ligand_ddg", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `command_template` | `Optional[List[str]]` | `None` | — |
| `cloud` | `bool` | `false` | — |
| `rosetta_bin` | `str` | _运行时计算_ | rosetta_scripts 可执行文件路径 |
| `protocol` | `str` | `"<repo>/src/blocks/scripts/ddg_protocol.xml"` | Rosetta XML 协议文件路径 |
| `flags` | `str` | `"<repo>/src/blocks/scripts/flags_rescore_genpot"` | Rosetta flags 文件路径 |
| `dalphaball_bin` | `str \| None` | _运行时计算_ | 内置 Holes filter 需要的 DAlphaBall 可执行文件；也会在 PATH 中查找。 |
| `override_param_file` | `str \| None` | `None` | 覆盖 -extra_res 用的配体 .params 文件路径。绕开按配体名自动解析。 |
| `override_ligand_names` | `list[str] \| None` | `None` | 覆盖配体三字母代码（如 ['FAD', 'IAI']）。绕开从结构元数据自动检测。使用每个结构原子数组中第一个匹配到的名字。 |
| `ligand_map` | `dict[str, str] \| None` | `None` | 检测和写 PDB 之前重命名原子数组中的配体残基。旧 res_name -> 新 res_name，如 {'LIG': 'FAD'}。在所有其他解析之前原地应用。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
