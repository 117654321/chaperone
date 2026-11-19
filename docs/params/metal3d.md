# metal3d

## 干什么用的

用 3D-CNN 预测过渡金属结合位点。

## 什么时候用它

找蛋白里的金属结合位点，或验证设计是否引入了金属位点。

## 基本信息

- **一句话**：Predict transition-metal binding sites with the Metal3D 3D-CNN
- **执行方式**：容器（`metal3d`）
- **需要上游输入**：是
- **容器入口**：`python /home/user/software/chaperone/src/blocks/scripts/run_metal3d.py`

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("metal3d", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--metal3d.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("metal3d", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `command_template` | `Optional[List[str]]` | `None` | — |
| `cloud` | `bool` | `false` | — |
| `metalbinding` | `bool` | `true` | True 时只对侧链能配位金属的残基做体素化（HIS/CYS/ASP/GLU/ASN/GLN/MET）。False 时扫描蛋白中每个 CA（慢很多）。 |
| `cluster_threshold` | `float` | `7.0` | 同一簇内探针体素之间的最大距离（Å）。值越大越容易把邻近位点并成一个。 |
| `pthreshold` | `float` | `0.1` | 体素成为簇种子所需的最小概率。值越低产生的位点越多（也越嘈杂）。 |
| `batch_size` | `int` | `128` | 推理批大小（体素盒数量）。 |
| `write_cube` | `bool` | `false` | True 时额外为每个输入写出体素概率图的 .cube 文件。默认关闭——文件可能很大。 |
| `compile_as_metric` | `bool` | `true` | True（默认）时把 Metal3D 指标挂到父行，不把 probefile 加入谱系——与预测 block 的 compile_as_metric 同一约定。设为 False 则把 probefile 当作谱系中的新结构。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
