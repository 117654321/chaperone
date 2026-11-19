# nanoparticle_prepare

## 干什么用的

对齐抗原碰撞参考，并保住 C3 骨架的对称轴。

## 什么时候用它

纳米颗粒/铁蛋白载体设计的准备步骤。

## 基本信息

- **一句话**：Align antigen clash reference and preserve a C3 scaffold's symmetry axis
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("nanoparticle_prepare", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--nanoparticle_prepare.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("nanoparticle_prepare", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `motif_pdb` | `str` | **必填** | 原始 RFdiffusion C3 抗原短桩 |
| `clash_ref_pdb` | `str` | **必填** | 短桩坐标系下的完整抗原茎部 |
| `max_clashes` | `int` | `8` | — |
| `max_c3_rmsd` | `float` | `2.0` | — |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
