# chirality_check

## 干什么用的

逐原子对比 CIP 手性码，检查预测的配体手性对不对。

## 什么时候用它

担心模型把配体手性搞错时。

## 基本信息

- **一句话**：Per-atom CIP-code chirality comparison vs a reference ligand
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("chirality_check", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--chirality_check.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("chirality_check", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `reference_cif` | `str` | **必填** | 带键记录的参考配体结构（CIF/PDB）路径。参考中的原子名必须与该行配体的原子名一致。 |
| `ligand_chain` | `Optional[str]` | `None` | 行结构中配体原子的链 ID。None 时通过 `hetero` 注释自动检测（hetero=True 的原子即配体）。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
