# ligand_pocket

## 干什么用的

配体接触、包埋、外壳的分布式指标。

## 什么时候用它

评估口袋的包埋程度和形状匹配。

## 基本信息

- **一句话**：Distributed ligand contact, enclosure, and shell metrics
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("ligand_pocket", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--ligand_pocket.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("ligand_pocket", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `ligand_resnames` | `list[str]` | **必填** | 要测量的配体残基名，如 ['ADN']。 |
| `core_atom_names` | `list[str]` | _运行时计算_ | 必须全部获得蛋白接触的配体核心原子。 |
| `tail_polar_atom_names` | `list[str]` | _运行时计算_ | 需要显式极性支撑的配体尾部原子。 |
| `contact_distance` | `float` | `5.0` | 定义覆盖范围与外壳的蛋白重原子距离。 |
| `polar_distance` | `float` | `3.6` | 定义极性支撑的蛋白 N/O/S 最大距离。 |
| `clash_distance` | `float` | `2.0` | 蛋白-配体重原子距离小于此值即计为严重碰撞。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
