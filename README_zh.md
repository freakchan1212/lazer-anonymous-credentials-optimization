# LaZer 匿名凭证正常证明路径实现优化——公开代码与数据

这是论文 **《Optimizing LaZer Anonymous Credentials for Repeated Presentation and Selective Disclosure》** 的实验复现仓库（第二篇小论文），**不包含第一篇“有界响应偏移修复”研究**。

## 内容与复现入口

- `project/`：LaZer/BLNS C、Python 源码、参数、构建与优化分支；没有预编译的原生库。
- `results/full/raw/`：本论文主实验完整原始 JSONL 数据与校验回执；记录包含 7200 次正式主实验会话。
- `results/full/artifacts/`：7 个记录变体的参数与关键源文件快照，用于同机代码差异和安全参数核对。
- `figures/`：英文和中文的图1—7，均有 SVG/PDF/PNG。
- `tables/`、`publication/final_tables.json`：正文数值和表格快照。
- `reproduce_final.py`：**直接根据原始 full 数据重算论文数字和全部图片**，不需要编译 LaZer。
- `check_regressions.py`：原始快照/参数的 11 项有限回归核查。

建议 Ubuntu 22.04 / Python 3.10+ 环境。绘中文图需要操作系统安装 CJK 字体，例如 `sudo apt install fonts-noto-cjk`；不随仓库分发字体文件。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-plots.txt
python verify_repository.py
python reproduce_final.py --output reproduced
python check_regressions.py --output regression_checks.json
```

已在本次清理后验证：主实验正式样本 7200，全部记录 13972；图 42 个文件生成成功；原版展示单元 327 项、终稿数值 256 项核查通过（有一处原有末位舍入备注）。**这是原始数据重建，不等同于重跑原生 full 试验或整协议安全验证。**

需要重新运行原生密码实验时，在满足系统 GMP/MPFR、编译器、CMake、Python/CFFI 等依赖后进入 `project/`：先 `bash 01_build.sh`，通过后再 `bash 02_run_smoke.sh`、`bash 03_run_pilot.sh 30`，确认环境正常再决定是否执行新的 full。此次公开整理未重新测试原生编译和完整性能实验。

主论文的性能结论是**本地证明生成+本地验证**，不含签发和网络开销。紧致化在特定应用关系下保持见证存在性，并不等于重新证明整协议安全。旧 E3 历史 raw full 不在包中，有些历史表仅保留原稿转录，详见自动生成的表格来源说明。

`MANIFEST_SHA256.txt` 验证公开文件字节未改变；`project/lazer/LICENSE` 是上游 LaZer 的许可，不能自动代替作者新写代码的许可。上架前由权利人确认拟采用的仓库开源许可。清理明细参见 `CLEANUP_REPORT.md`。
