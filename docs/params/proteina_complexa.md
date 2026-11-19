# proteina_complexa

## 干什么用的

全原子蛋白 binder 序列/结构联合设计。

## 什么时候用它

需要全原子精度（含侧链）的复合物设计。

## 基本信息

- **一句话**：All-atom protein binder sequence/structure co-design
- **执行方式**：容器（`proteina_complexa`）
- **需要上游输入**：否（源 block）
- **容器入口**：`python -m proteinfoundation.generate`

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("proteina_complexa", inputs="<输入路径>", <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--proteina_complexa.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("proteina_complexa", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `command_template` | `Optional[List[str]]` | `None` | — |
| `cloud` | `bool` | `false` | — |
| `target_pdb` | `str` | **必填** | 靶点 PDB；会复制进每个 job 沙盒 |
| `target_selection` | `str` | **必填** | 上游靶点输入规格，如 A1-115 |
| `hotspots` | `list[str]` | **必填** | 靶点残基标识，如 ['A37', 'A39'] |
| `binder_length` | `tuple[int, int]` | `[80, 120]` | binder 残基数闭区间 |
| `num_designs` | `int` | `1` | 每批生成的设计数 |
| `n_batches` | `int` | `1` | 独立引擎作业，各用不同种子 |
| `batch_size` | `int` | `1` | 单 GPU 上的并发样本数 |
| `num_steps` | `int` | `400` | flow 积分步数；上游默认 400 |
| `seed` | `int` | `0` | 基础种子，按引擎 chunk ID 递增 |
| `checkpoint_dir` | `str` | **必填** | 存放公开 complexa.ckpt 与 complexa_ae.ckpt 的目录 |

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
