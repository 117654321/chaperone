# Chaperone block 总览

87 个 block 的中文说明。每个文件里还有完整参数表、调用方式和例子。

重新生成：`python scripts/export_param_docs.py`

## 骨架生成

| block | 干什么 |
|---|---|
| [`rfd1`](rfd1.md) | RFdiffusion v1：骨架层面蛋白设计 |
| [`rfd2`](rfd2.md) | RFdiffusion2：原子级蛋白设计，支持配体、小分子 |
| [`rfd3`](rfd3.md) | RFdiffusion3：通用扩散设计 |
| [`rfd3na`](rfd3na.md) | RFdiffusion3NA：全原子蛋白/DNA/RNA 设计 |
| [`rfd3_partial`](rfd3_partial.md) | RFdiffusion3 部分扩散：从已有结构出发，加噪声再生成，做多样化或细化 |
| [`rfd4`](rfd4.md) | RFD4-Proteina：flow matching 生物分子设计，条件化能力最强（热点、埋藏、氢键、二级结构） |

## 搜索与优化

| block | 干什么 |
|---|---|
| [`rfd4_search`](rfd4_search.md) | RFD4-Proteina 奖励引导束搜索：生成过程中就分叉、用 AF3 oracle 给每个分支打界面分，只保留胜者继续采样 |

## 端到端设计

| block | 干什么 |
|---|---|
| [`bindcraft`](bindcraft.md) | AF2 引导的从头 binder 设计 |
| [`bindcraft2`](bindcraft2.md) | BindCraft 第二代：JAX 优化 + ProteinMPNN 重设计 + AF2 验证 |
| [`protein_hunter`](protein_hunter.md) | Boltz 结构幻觉做从头 binder 设计 |
| [`boltzgen`](boltzgen.md) | BoltzGen 蛋白设计：扩散生成骨架 + 逆向折叠 + 结构验证 |
| [`disco`](disco.md) | 蛋白序列-结构联合设计，可条件化在配体上 |
| [`proteina_complexa`](proteina_complexa.md) | 全原子蛋白 binder 序列/结构联合设计 |
| [`rfoptimization`](rfoptimization.md) | RF3 梯度 / Boltz-2 循环 + 外部 MPNN 序列重设计 |

## 序列设计

| block | 干什么 |
|---|---|
| [`mpnn`](mpnn.md) | LigandMPNN / ProteinMPNN 逆向折叠：给骨架设计序列 |
| [`foundry_mpnn`](foundry_mpnn.md) | Foundry 版 MPNN 逆向折叠（ProteinMPNN / LigandMPNN / SolubleMPNN） |
| [`esm2`](esm2.md) | ESM-2 蛋白语言模型，输出序列嵌入向量 |
| [`e1`](e1.md) | E1 掩码语言模型，做序列预测 |

## 结构预测

| block | 干什么 |
|---|---|
| [`af3`](af3.md) | AlphaFold3 结构预测 |
| [`af3_with_target_template`](af3_with_target_template.md) | AlphaFold3，但把靶点链的结构固定成模板 |
| [`boltz2`](boltz2.md) | Boltz-2 结构预测，支持蛋白、配体、复合物，还能做亲和力预测 |
| [`boltz2_steered`](boltz2_steered.md) | Boltz-2 加螺旋引导（跑在 protein_hunter 容器里） |
| [`chai1`](chai1.md) | Chai-1 结构预测 |
| [`colabfold`](colabfold.md) | ColabFold（AlphaFold2 封装），支持 MSA 服务器和本地 MSA |
| [`esmfold2`](esmfold2.md) | ESMFold2 结构预测，可选 MSA 条件化 |
| [`openfold3`](openfold3.md) | OpenFold3 结构预测（AF3 的开源实现） |
| [`protenix`](protenix.md) | Protenix 结构预测 |
| [`rf3`](rf3.md) | RosettaFold3 结构预测 |
| [`simplefold`](simplefold.md) | Apple SimpleFold：只吃序列的蛋白单体折叠预测 |

## 打分与筛选

| block | 干什么 |
|---|---|
| [`filter`](filter.md) | 按指标阈值或分位数筛行 |
| [`ipsae`](ipsae.md) | ipSAE 界面打分——用对齐误差评估界面置信度 |
| [`mpnn_score`](mpnn_score.md) | 解析 MPNN FASTA 里的置信度，变成可排序的指标 |
| [`peppr`](peppr.md) | 用 peppr 算结构评估指标：fnat、irmsd、lrmsd、dockq、lDDT |
| [`rmsd`](rmsd.md) | 算两个结构之间的对齐 RMSD（骨架、全原子、motif） |
| [`tm_score`](tm_score.md) | 对参考结构算 TM-score |
| [`tm_score_rna`](tm_score_rna.md) | TM-score_RNA（Gong 2019），用 US-align 算，按参考长度归一化 |
| [`ppi_ddg`](ppi_ddg.md) | FastRelax + ddG 算蛋白-蛋白结合能 |
| [`ligand_ddg`](ligand_ddg.md) | Rosetta DDG 计算蛋白-配体结合能 |
| [`ligand_ddg_soft`](ligand_ddg_soft.md) | 软排斥版 ddG：硬打包、软打分、截尾均值 |
| [`tmol_interface`](tmol_interface.md) | tmol 算蛋白-配体界面 ddG 和逐项能量分解 |
| [`tmol_minimize`](tmol_minimize.md) | tmol 笛卡尔全原子能量最小化（beta_nov2016_cart） |

## 结构与注释

| block | 干什么 |
|---|---|
| [`to_cif`](to_cif.md) | 把结构重新保存成 CIF |
| [`to_pdb`](to_pdb.md) | 把结构重新保存成 PDB |
| [`transform`](transform.md) | 对每行应用 atomworks Transform |
| [`annotate`](annotate.md) | 给结构加注释：界面残基、氢键、配体邻域芳香残基 |
| [`copy`](copy.md) | 复制设计行，用于测试血缘追踪 |
| [`select_chains`](select_chains.md) | 保留指定链，残基编号和血缘不变 |
| [`restore_sidechains`](restore_sidechains.md) | 从上游结构恢复指定 motif 的 rotamer |
| [`materialize`](materialize.md) | 把存储的结构（catcif 归档）写到磁盘 |

## 其他

| block | 干什么 |
|---|---|
| [`aromatic_neighbors`](aromatic_neighbors.md) | 数配体原子周围有多少芳香残基 |
| [`chirality_check`](chirality_check.md) | 逐原子对比 CIP 手性码，检查预测的配体手性对不对 |
| [`clash`](clash.md) | 数骨架重原子之间的非成键碰撞 |
| [`contact_ms`](contact_ms.md) | 计算 binder 和靶点之间的接触分子表面积（CMS） |
| [`dssr_motif_base_pairing`](dssr_motif_base_pairing.md) | 用 DSSR 检查 motif 碱基配对，看原生分类是否保留 |
| [`dssr_snap_metrics`](dssr_snap_metrics.md) | 用 x3dna-dssr 和 x3dna-snap 算蛋白-DNA 复合物的生物物理指标 |
| [`foldseek`](foldseek.md) | 用 Foldseek 按结构相似度聚类 |
| [`hbond_metrics`](hbond_metrics.md) | 算配体相互作用的氢键指标 |
| [`ingest`](ingest.md) | 从各种来源导入数据（DataFrame、CSV、Parquet、结构路径列表） |
| [`ligand_clash`](ligand_clash.md) | 量蛋白和配体之间最近的重原子接触距离 |
| [`ligand_pocket`](ligand_pocket.md) | 配体接触、包埋、外壳的分布式指标 |
| [`manifest_val_structures`](manifest_val_structures.md) | 为验证集准备 PDB 参考组装体 |
| [`metal3d`](metal3d.md) | 用 3D-CNN 预测过渡金属结合位点 |
| [`motif_confidence`](motif_confidence.md) | 按 diffused_index_map 拆出 motif 和骨架各自的 pLDDT / PAE |
| [`motif_geometry`](motif_geometry.md) | 算 motif 原子之间的距离和角度 |
| [`mutate_residues`](mutate_residues.md) | 按指定残基生成命名变体，血缘清晰 |
| [`nanoparticle_prepare`](nanoparticle_prepare.md) | 对齐抗原碰撞参考，并保住 C3 骨架的对称轴 |
| [`order_collection`](order_collection.md) | 提取序列、检查订购状态、汇总指标 |
| [`package_submission`](package_submission.md) | 校验并写出只含序列的提交包 |
| [`plip`](plip.md) | 用 PLIP 分析蛋白-配体相互作用类型（氢键、疏水、π 堆积等） |
| [`pocket_coulomb`](pocket_coulomb.md) | 算带电配体原子和带电口袋残基之间的静电互补性 |
| [`rasa`](rasa.md) | 算配体原子的溶剂可及表面积 |
| [`reference_motif_rmsd`](reference_motif_rmsd.md) | 按 diffused_index_map 算 motif 相对输入的 RMSD |
| [`remap_ligand`](remap_ligand.md) | 把预测输出的配体原子/残基名改成和参考 CIF 一致 |
| [`rna_connectivity`](rna_connectivity.md) | 检查核酸链的 O3'(i)→P(i+1) 骨架断裂 |
| [`rna_ss_f1_mcc`](rna_ss_f1_mcc.md) | 用 RNet2 预测的二级结构和参考规范配对算 F1 / MCC |
| [`rna_thermo`](rna_thermo.md) | 用 ViennaRNA 算 Boltzmann 概率、配对概率、集合缺陷 |
| [`rotamer_metrics`](rotamer_metrics.md) | 算蛋白侧链的 rotamer 质量（要 Dunbrack 库） |
| [`rotamer_relax`](rotamer_relax.md) | 用 PyRosetta 做 rotamer 松弛 |
| [`rotamer_sweep`](rotamer_sweep.md) | 穷举指定侧链的 chi 角度组合 |
| [`rpxdock`](rpxdock.md) | 把 C3 不对称单元对接到 I3 笼子里，输出 C3 三聚体 |
| [`score_val_structures`](score_val_structures.md) | 用验证参考给预测结构打分 |
| [`secondary_structure`](secondary_structure.md) | 算二级结构组成，以及配体周围口袋的 loop / pLDDT 无序度 |
| [`select_diverse`](select_diverse.md) | 按序列/结构阈值选多样性子集 |
| [`select_motif`](select_motif.md) | 用自定义函数挑 motif 残基，供下游固定 |
| [`selective_sidechain_repack`](selective_sidechain_repack.md) | 只重打包明确选中的蛋白侧链 |
| [`sequence_identity_gate`](sequence_identity_gate.md) | 骨架区域对天然参考的全局 NW 一致性，作为新颖性硬门槛 |
| [`symmetry`](symmetry.md) | 算同源寡聚体组装相对循环点群的偏差 |
