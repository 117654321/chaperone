# bindcraft

## 干什么用的

AF2 引导的从头 binder 设计。幻觉生成 binder + ProteinMPNN 重设计 + AF2 验证，全自动串起来。

## 什么时候用它

想一条命令出 binder，不想自己搭流水线。单条轨迹约 3 分钟，整轮可能几小时。

## 基本信息

- **一句话**：AlphaFold2-guided de novo protein binder design
- **执行方式**：容器（`bindcraft`）
- **需要上游输入**：是
- **容器入口**：`python -u /opt/BindCraft/chaperone_run_bindcraft.py`

## 怎么调用

```python
from chaperone import ExecutionEngine, init_cli
init_cli()
engine = ExecutionEngine(rundir="out")
h = engine.run("bindcraft", data=upstream_handler, <参数>=<值>)
```

参数三种传法，优先级从高到低：

| 方式 | 写法 | 用途 |
|---|---|---|
| 命令行 | `--bindcraft.参数名=值` | 临时试，不改代码 |
| 配置文件 | `--config=my.yaml`（`参数名: 值`，按 block 名分组） | 批量改、存版本 |
| 脚本 kwargs | `engine.run("bindcraft", 参数名=值)` | 最常用 |

## 全部参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `store` | `Literal['none', 'catcif']` | `"none"` | 编译后合并输出。``'none'`` 不存储；``'catcif'`` 写成一个拼接的 CIF 归档。 |
| `store_cleanup` | `bool` | `false` | ``store='catcif'`` 时，文件并入归档后删除沙盒里的输出文件。其他情况忽略。 |
| `command_template` | `Optional[List[str]]` | `None` | — |
| `cloud` | `bool` | `false` | — |
| `chains` | `str` | **必填** | BindCraft 靶点链选择器，如 'A' 或 'A,B'。 |
| `target_hotspot_residues` | `str \| None` | `None` | hotspot 选择，如 'A56,A60-64'；None 自动选位点。 |
| `lengths` | `tuple[int, int]` | `[65, 150]` | binder 长度的闭区间上下限。 |
| `number_of_final_designs` | `int` | `1` | 每个输入靶点要求的接受设计数。 |
| `max_trajectories` | `int \| None` | `100` | 每个靶点最大*成功*幻觉轨迹数。BindCraft 只统计进入 relax 步骤（Trajectory/Relaxed/）的轨迹，所以早期轨迹全部没过 pLDDT>=0.7 门槛时会一直生成新轨迹。None 沿用 advanced preset。 |
| `binder_name` | `str` | `"binder"` | 生成设计的名称前缀。 |
| `trajectory_budget_hours` | `float \| None` | `12.0` | 设计循环的墙钟预算。BindCraft 的 max_trajectories 只计成功轨迹，早期都失败时会无限循环；到达预算就停止运行，`Accepted/` 里已有的设计保留。应小于 Slurm 的 time_limit。 |
| `filter_preset` | `str` | `"default_filters"` | 内置 BindCraft 过滤 preset 的文件名。 |
| `advanced_preset` | `str` | `"default_4stage_multimer"` | 内置 BindCraft 高级设置 preset 的文件名。 |
| `filters_path` | `str \| None` | `None` | 自定义 filters JSON（可选），覆盖 filter_preset。 |
| `advanced_path` | `str \| None` | `None` | 自定义 advanced JSON（可选），覆盖 advanced_preset。 |
| `af_params_dir` | `str \| None` | _运行时计算_ | 存放 AlphaFold2 参数 .npz 的目录，挂载到 /opt/BindCraft/params。镜像里该目录是空的。默认取 BINDCRAFT_AF2_PARAMS，与 bindcraft2 共用。 |

## `filter_overrides`

对所选 filter JSON 做浅层覆盖。

这是上游设置的浅层覆盖字典，整体替换而不是逐项合并。

## `advanced_overrides`

对所选 advanced JSON 做浅层覆盖。

这是上游设置的浅层覆盖字典，整体替换而不是逐项合并。

## 由脚本提供的参数

这些不写进参数表，运行时由引擎或你的脚本传入：

| 参数 | 谁提供 |
|---|---|
| `data` | 引擎：`engine.run(..., data=上游handler)` |
| `name` | 可选，默认就是 block 名；同类型用两次才需要改名 |
