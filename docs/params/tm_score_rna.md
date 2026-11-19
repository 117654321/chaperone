# tm_score_rna

## 干什么用的

TM-score_RNA（Gong 2019），用 US-align 算，按参考长度归一化。

## 什么时候用它

RNA 结构相似度。参考长度 < 20 时改用 RMSD。

## 基本信息

- **一句话**：TM-score_RNA (Gong 2019) against a reference fold via US-align, normalized by the reference length
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("tm_score_rna", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--tm_score_rna.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("tm_score_rna", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `reference` | `str` | **必填** | 参考结构路径（天然折叠）。 |
| `reference_chain` | `Optional[str]` | `None` | 把参考限制到单链。None 保留全部链并作为一个整体对齐（-ter 0）。 |
| `chain` | `Optional[str]` | `None` | 把设计限制到单链。None 使用全部。 |
| `expected_reference_length` | `Optional[int]` | `None` | 参考应解析出的核苷酸数。在 setup 阶段检查——解析错会静默改变 d0，进而改变所有分数。 |
| `fixed_correspondence` | `bool` | `false` | 按给定的残基下标对应关系打分（-TMscore 1），不搜索比对。仅当设计与参考编号一致时有意义。 |
| `mol` | `str` | `"RNA"` | US-align 分子类型：RNA 或 prot。 |
| `usalign_binary` | `Optional[str]` | `None` | US-align 可执行文件名或路径。依次回退到 USALIGN_BIN 设置、venv 的 bin、PATH。 |
| `min_reference_length` | `int` | `30` | 参考短于此长度就拒绝。L 接近 18 时 d0 趋于零，TM-score_RNA 在短选择上无定义——那种情况请用 RMSD。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
