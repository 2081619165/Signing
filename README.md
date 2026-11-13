# Signing
Windows 印签处理工具的算法验证项目。当前完成 V1 灰底签名与 V2 可选自然锐化实验，尚无正式应用、GUI 或 EXE；红章仅做上游算法实验，蓝章及自动类型识别未实现。

## 当前目录与入口
- experiments/gray_signature.py：V1 灰底去除，原尺寸RGBA及400×200实验画布；不是独立命令行入口。
- experiments/signature_sharpen.py：V2 Alpha分析、可选锐化与回退；暂含黑签GIF导出。
- experiments/compare_gray.py：实验编排；保留上游对照、三背景预览、GIF与JSON。
- experiments/run.py、fetch_sources.py：第一阶段实验及固定SHA源码获取。
- experiments/write_report.py：历史文档生成器，禁止再次运行，会覆盖当前文档。
- experiments/licenses/show7-MIT.txt：上游版权和许可；不代表Signing整体已选择MIT。
- .local-tests/：忽略的源码快照、测试样本和全部输出；不得提交。
- docs/：进度、问题、决策、检查、日志与第一阶段审查。
当前无正式算法包、业务层、GUI模块或依赖清单；正式目录仅为后续规划。

## 现有实验运行（PowerShell）
```powershell
Set-Location -LiteralPath 'D:\code\Signing'
python 'D:\code\Signing\experiments\compare_gray.py'
# 关闭锐化：
python 'D:\code\Signing\experiments\compare_gray.py' --no-sharpen
```
真实本地输入目前固定读取 D:\code\signature-extractor\input（PNG/JPG/JPEG）；.local-tests/private-input尚未接入。依赖OpenCV、NumPy、Pillow；原版对照还要求.local-tests/signature-extractor快照。第一阶段另一算法需要SciPy，不是未来正式运行的必需依赖。全新检出不能只运行对比命令：先准备依赖和快照；历史合成样本可运行run.py生成。
输出在 D:\code\Signing\.local-tests\gray-v2，关闭输出gray-v2-off，历史gray-v1保留。每组original、baseline、optimized_native、sharpened_native、三背景预览、comparison.jpg及signature.gif（空白跳过）；results.json记录失败与回退。重复运行覆盖同名结果。
默认签名GIF高42px（1.1cm、96DPI取整），单级透明阈值128；淡灰GIF全透明是已知失败，不能当成合格导出。视觉质量均需人工验收。

架构规划见 docs/DECISIONS.md；当前状态以 PROGRESS、BUGS、CHECK_REPORT为准，REVIEW.md只记录第一阶段。未提交或推送；Git操作须由用户确认执行。
