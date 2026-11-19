# ligand_ddg_soft

## 干什么用的

软排斥版 ddG：硬打包、软打分、截尾均值。

## 什么时候用它

配体-蛋白界面比较紧张时，硬排斥算不出结果可以用这个。

## 基本信息

- **一句话**：Soft-repulsive ddG (pack hard, score soft, trimmed mean)
- **执行方式**：纯 Python
- **需要上游输入**：是

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("ligand_ddg_soft", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--ligand_ddg_soft.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("ligand_ddg_soft", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `replicates` | `int` | `5` | pack+score 循环次数。≥3 时用截尾均值（去掉最好和最差）。 |
| `binder_chain` | `str` | `"A"` | binder 的链 ID。 |
| `ligand_chain` | `str` | `"B"` | 配体的链 ID。 |
| `interesting_atoms` | `list[str] \| None` | `None` | 要保留的配体重原子名（连同其成键氢）。参数文件由该子集生成。 |
| `ph` | `float` | `7.4` | 对无氢配体运行 Dimorphite-DL 质子化的目标 pH。 |
| `override_params_file` | `str \| None` | `None` | 现成的 .params 文件。绕开质子化和参数生成——配体的氢必须已经对得上。 |
| `ref_smiles` | `str \| None` | `None` | 当原子名不符合 CCD 规范时，用于重建配体键图的参考 SMILES（扩散输出中很常见）。默认按配体残基名查 CCD。 |
| `cleanup_params_cache` | `bool` | `true` | 最后一个块退出时删除共享参数缓存。 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
