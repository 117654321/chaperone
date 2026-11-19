# package_submission

## 干什么用的

校验并写出只含序列的提交包。

## 什么时候用它

把设计交给合成公司前的格式化输出。

## 基本信息

- **一句话**：Validate and write a sequence-only design submission
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("package_submission", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--package_submission.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("package_submission", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `output_dir` | `str` | **必填** | 写入 designs.csv（及 run_meta.json）的目录 |
| `expected_count` | `Optional[int]` | `None` | 要求的精确设计数；None 表示数量不限 |
| `sequence_key` | `str` | `"sequence"` | 存放氨基酸序列的列。默认解析标准的 sequence_<CHAIN> 列以及由结构支撑的蛋白序列。 |
| `allow_duplicates` | `bool` | `false` | 允许序列重复（关闭时重复即违规） |
| `metadata` | `Optional[dict]` | `None` | 原样写入 run_meta.json；None 时省略 |
| `extra_columns` | `Optional[list[str]]` | `None` | 除序列外还要带进 designs.csv 的额外列 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
