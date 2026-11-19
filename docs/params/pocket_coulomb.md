# pocket_coulomb

## 干什么用的

算带电配体原子和带电口袋残基之间的静电互补性。

## 什么时候用它

评估静电匹配好不好，尤其是带电配体。

## 基本信息

- **一句话**：Electrostatic complementarity between charged ligand atoms and charged pocket residues
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("pocket_coulomb", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--pocket_coulomb.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("pocket_coulomb", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `pocket_radius` | `float` | `8.0` | 定义配体周围口袋残基的 CB 距离截断（Å） |
| `distance_floor` | `float` | `1.5` | 防止碰撞导致奇点的最小距离（Å） |
| `distance_cutoff` | `float` | `12.0` | 忽略距任一带电配体原子超过此距离（Å）的带电蛋白原子 |
| `power` | `float` | `2.0` | 库仑式衰减的距离指数（2.0 相当于隐式溶剂屏蔽） |
| `ref_smiles` | `Optional[str]` | `None` | 原子名不符合 CCD 规范时用于重建配体键图的参考 SMILES（扩散模型输出） |
| `per_residue` | `bool` | `false` | 在输出指标中包含逐残基分数分解 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
