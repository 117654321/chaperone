# restore_sidechains

## 干什么用的

从上游结构恢复指定 motif 的 rotamer。

## 什么时候用它

想保住 motif 的原始侧链构象，而不是重新打包。

## 基本信息

- **一句话**：Restore selected motif rotamers from an upstream structure
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("restore_sidechains", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--restore_sidechains.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("restore_sidechains", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `positions_json` | `str` | **必填** | 把参考结构路径映射到残基位置的 JSON。 |
| `reference_index` | `int` | `0` | 参考结构在每行谱系中的下标。 |
| `align_backbone` | `bool` | `false` | 复制侧链前先把每个参考残基的骨架刚性对齐到当前骨架。用于骨架发生移动的预测或弛豫结构。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
