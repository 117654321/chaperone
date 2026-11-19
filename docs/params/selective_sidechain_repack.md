# selective_sidechain_repack

## 干什么用的

只重打包明确选中的蛋白侧链。

## 什么时候用它

想改进部分侧链但保持其他不变。

## 基本信息

- **一句话**：Repack only explicitly selected protein sidechains
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("selective_sidechain_repack", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--selective_sidechain_repack.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("selective_sidechain_repack", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `positions` | `list[str]` | _运行时计算_ | 要重打包的蛋白残基 ID，如 ['A42', 'A:73']。 |
| `clash_distance` | `float \| None` | `None` | 设置后，还会检测并重打包每个结构中、非成键蛋白重原子接触距离小于此值的残基。 |
| `sequence_separation` | `int` | `1` | 碰撞检测中排除的同链残基间隔。 |
| `scorefxn_name` | `str` | `"beta_nov16"` | 挑选固定身份 rotamer 时使用的 Rosetta 打分函数。 |
| `extra_rotamers` | `bool` | `true` | 在选定位置做额外的 chi1-chi4 采样。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
