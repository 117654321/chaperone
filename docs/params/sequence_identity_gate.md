# sequence_identity_gate

## 干什么用的

骨架区域对天然参考的全局 NW 一致性，作为新颖性硬门槛。

## 什么时候用它

确保设计不是照抄天然序列。RNA motif 支撑 benchmark 用 0.40 阈值。

## 基本信息

- **一句话**：Global NW identity of the scaffold region against natural references; hard novelty gate
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("sequence_identity_gate", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--sequence_identity_gate.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("sequence_identity_gate", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `references` | `str` | **必填** | 用于比对的天然序列 FASTA——天然构建体加 Rfam/RNAcentral 同源序列。 |
| `threshold` | `float` | `0.4` | 设计可通过的最大骨架一致性。按项目设定；0.40 是 RNA motif 支撑 benchmark 的取值。 |
| `exclude_motif` | `bool` | `true` | 只对骨架区域打分。保持 True——motif 一致性按构造就是 100%，纳入后这道门槛就失去意义。 |
| `chain` | `Optional[str]` | `None` | 限定到某一个链 id。None 使用所有 RNA 残基。 |
| `compute_intra_identity` | `bool` | `false` | 同时报告与本块其他任何设计的最大一致性，用来判断设计器是在探索还是在输出近似副本。O(n²) 次比对，默认关闭。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
