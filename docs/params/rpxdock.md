# rpxdock

## 干什么用的

把 C3 不对称单元对接到 I3 笼子里，输出 C3 三聚体。

## 什么时候用它

纳米颗粒/笼状载体的对接设计。

## 基本信息

- **一句话**：Dock a z-oriented C3 asymmetric unit into an I3 cage and emit C3 trimers
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("rpxdock", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--rpxdock.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("rpxdock", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `command_template` | `Optional[List[str]]` | `None` | — |
| `cloud` | `bool` | `false` | — |
| `nout_top` | `int` | `1` | 每个输入取最高分的 C3 三聚体数量 |
| `beam_size` | `int` | `10000` | RPXdock 层次搜索的 beam 大小 |
| `ignored_aas` | `str` | `"CGP"` | RPX 打分排除的残基类型；聚甘氨酸占位骨架请用空字符串。 |
| `cache_dir` | `str` | _运行时计算_ | RPXdock 打分与对称缓存的解压后存放目录（可写）。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
