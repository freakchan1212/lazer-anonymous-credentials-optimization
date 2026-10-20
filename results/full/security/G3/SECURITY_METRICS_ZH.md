# 安全指标：原配置证据与固定模型估计（当前变体：G3）

原装生成器目标128位，协议参数集变更标志：`protocol_parameters_changed = False`。以下攻击成本是声明范围内的启发式估计，不能当作整套协议已证明位数。

| 分量 | 攻击 | RHF δ0 | beta | 经典log2成本 | 量子log2成本 |
|---|---|---:|---:|---:|---:|
| P1_MSIS | generic_SIS_subdimension_GSA | 1.0043951 | 347 | 101.324 | 91.955 |
| P1_MLWE | primal_uSVP_GSA | 1.0043734 | 350 | 102.200 | 92.750 |
| P2_MSIS | generic_SIS_subdimension_GSA | 1.0043793 | 349 | 101.908 | 92.485 |
| P2_MLWE | primal_uSVP_GSA | 1.0043146 | 356 | 103.952 | 94.340 |
| Falcon_NTRU_preimage_generic | generic_SIS_subdimension_GSA | 1.0038778 | 416 | 121.472 | 110.240 |

模型：ADPS16_CoreSVP_C0.292_Q0.265_no_BKZ_overhead。MLWE采用三元均匀秘密/误差、无限样本的无结构模型。Falcon/NTRU行仅是通用格原像攻击代理。

| 安全指标 | 证据类型 | 内容 | 边界 |
|---|---|---|---|
| 经典攻击成本 | MODEL_ESTIMATE | attack_costs.csv: classical_log2_cost | minimum only within declared attacks; not certified whole-protocol bits |
| 量子攻击成本 | MODEL_ESTIMATE | attack_costs.csv: quantum_log2_cost | not half of classical bits; excludes quantum algorithm overhead and structured attacks |
| 不可伪造性 | UPSTREAM_CONDITIONAL_PROPERTY | original BLNS-style construction retained | auxiliary-preimage assumption, extraction and reduction required; no independently instantiated numeric advantage/query bound |
| 匿名性与不可关联性 | UPSTREAM_CONDITIONAL_PROPERTY | hidden blocks [1,2,3,6,7]; disclosed blocks [0,4,5]; fresh proof randomness | revealed attributes may identify users; no traffic anonymity or arbitrary collusion claim; unique proof hashes are only a randomness regression check |
| 证明知识可靠性 | UPSTREAM_BOUND_AND_FORMULA_RECOMPUTATION | P1 and P2 header epsilon <= 2^-127 under MSIS | interactive proof declaration; not full Fiat-Shamir/QROM advantage after hash queries/extraction losses |
| 零知识误差 | UPSTREAM_COMPUTATIONAL_SIMULATION_ASSUMPTION | P1 MLWE(26,29,[-1,1]); P2 MLWE(32,32,[-1,1]) | no standalone numeric statistical-distance/full advantage bound instantiated; cannot infer from observed acceptance or KAPPA=128 |

逐项假设覆盖见assumption_coverage.csv。

## 知识错误公式复算

- P1: epsilon=3.67341985e-39, -log2(epsilon)=127.678072; 原头文件保守界2^-127；放大参数lambda=4；MSIS假设：MSIS(17,79,2^(33.599457))。
- P2: epsilon=3.67341985e-39, -log2(epsilon)=127.678072; 原头文件保守界2^-127；放大参数lambda=4；MSIS假设：MSIS(20,112,2^(40.173114))。
