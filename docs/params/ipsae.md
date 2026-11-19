# ipsae

## 干什么用的

ipSAE 界面打分——用对齐误差评估界面置信度。

## 什么时候用它

复合物排序首选。比单看 ipTM 更能反映真实界面质量。

## 基本信息

- **一句话**：Interface predicted Score from Aligned Errors
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("ipsae", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--ipsae.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("ipsae", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `binder_chain` | `str` | `"A"` | 设计 binder 的链 ID。默认 'A'，与 RFD3 输出一致。 |
| `target_chains` | `Optional[List[str]]` | `None` | 靶点的链 ID。None 时用预测中所有非 binder 链。 |
| `pae_cutoff` | `float` | `10.0` | 计入分数的 PAE 阈值（Å）。按 Park & Cong 默认 10.0。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
