# bindcraft2

## 干什么用的

BindCraft 第二代：JAX 优化 + ProteinMPNN 重设计 + AF2 验证。

## 什么时候用它

同 bindcraft，新版算法。

## 基本信息

- **一句话**：JAX binder optimization, ProteinMPNN redesign, and AlphaFold2 validation
- **执行方式**：容器（`bindcraft2`）
- **需要上游输入**：是
- **容器入口**：`bindcraft design`

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("bindcraft2", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--bindcraft2.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("bindcraft2", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `command_template` | `Optional[List[str]]` | `None` | — |
| `cloud` | `bool` | `false` | — |
| `chain` | `str` | **必填** | 输入结构中的单条靶点蛋白链 |
| `hotspots` | `str \| None` | `None` | 靶点残基编号/范围，如 54,56,66-70 |
| `lengths` | `tuple[int, int]` | `[60, 180]` | binder 长度闭区间 |
| `number_of_final_designs` | `int` | `1` | — |
| `max_trajectories` | `int` | `10` | 每个输入的有限优化预算；通过的设计不足则判失败 |
| `seed` | `int` | `42` | — |
| `af2_params_dir` | `str \| None` | `None` | 含全部 5 个 multimer-v3 和 2 个 PTM AF2 checkpoint 的目录；也可用 BINDCRAFT_AF2_PARAMS |
| `weights_dir` | `str` | _运行时计算_ | 未提供 AF2 目录时，上游权重下载用的可写缓存 |

## `overrides`

选定的上游科学设置；改 filter 等于改接受判据

这是上游设置的浅层覆盖字典，整体替换而不是逐项合并。

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
