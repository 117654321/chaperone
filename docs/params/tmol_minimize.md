# tmol_minimize

## 干什么用的

tmol 笛卡尔全原子能量最小化（beta_nov2016_cart）。

## 什么时候用它

把结构能量降下来，消除明显冲突。

## 基本信息

- **一句话**：tmol Cartesian all-atom energy minimisation (beta_nov2016_cart)
- **执行方式**：容器（`tmol`）
- **需要上游输入**：是
- **容器入口**：`python /home/user/software/chaperone/src/blocks/scripts/run_tmol.py`

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("tmol_minimize", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--tmol_minimize.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("tmol_minimize", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `command_template` | `Optional[List[str]]` | `None` | — |
| `cloud` | `bool` | `false` | — |
| `ligand_smiles` | `str \| None` | `None` | 配体的 SMILES。用于生成 tmol 的 .tmol 参数文件（仅做类型化——输入配体坐标按原样打分）。非规范配体必须提供，除非给了 ligand_params_files。 |
| `ligand_params_files` | `list[str] \| None` | `None` | 配体现成的 tmol .tmol 参数文件。最确定的类型化路径，绕开 SMILES 生成。 |
| `fix_backbone` | `bool` | `false` | 冻结骨架只最小化侧链（默认全部自由）。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
