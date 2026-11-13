# Signing
Windows 印签处理工具的算法验证项目。当前完成 V1 灰底签名与 V2 可选自然锐化实验，已有独立最小窗口原型，现已接入黑签单图闭环，尚无EXE；红章仅做上游算法实验，蓝章及自动类型识别未实现。

## 当前目录与入口
- experiments/gray_signature.py：V1 灰底去除，原尺寸RGBA及400×200实验画布；不是独立命令行入口。
- experiments/signature_sharpen.py：V2 Alpha分析、可选锐化与回退；暂含黑签GIF导出。
- experiments/compare_gray.py：实验编排；保留上游对照、三背景预览、GIF与JSON。
- experiments/run.py、fetch_sources.py：第一阶段实验及固定SHA源码获取。
- experiments/write_report.py：历史文档生成器，禁止再次运行，会覆盖当前文档。
- experiments/licenses/show7-MIT.txt：上游版权和许可；不代表Signing整体已选择MIT。
- .local-tests/：忽略的源码快照、测试样本和全部输出；不得提交。
- docs/：进度、问题、决策、检查、日志与第一阶段审查。
app/为独立窗口原型，含自己的依赖清单；正式算法包及业务层仍未创建。

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


## PyWebView 最小窗口原型（2026-11-13）
独立入口app/main.py，窗口/通信/JSONL诊断在app/window.py，静态资源在app/static/index.html、style.css、main.js。未接入印签算法，未改变experiments。app/requirements.txt锁定本次虚拟环境依赖（pywebview6.2.1/pythonnet3.2.1）；无Vue/React/Node/FastAPI或业务HTTP服务。Bottle是PyWebView传递依赖，安装不等于启动服务。

### 安装与启动（PowerShell）
```powershell
Set-Location -LiteralPath 'D:\code\Signing'
python -m venv 'D:\code\Signing\.venv'
& 'D:\code\Signing\.venv\Scripts\python.exe' -m pip install -r 'D:\code\Signing\app\requirements.txt'
& 'D:\code\Signing\.venv\Scripts\python.exe' 'D:\code\Signing\app\main.py' --check
& 'D:\code\Signing\.venv\Scripts\python.exe' 'D:\code\Signing\app\main.py'
```
无需激活虚拟环境。若--check报缺运行库，先安装微软WebView2 Evergreen Runtime（https://developer.microsoft.com/microsoft-edge/webview2/ ）及.NET Framework4.6.2或更高版本，然后重试；不自动下载安装系统组件。普通Edge浏览器不等于WebView2 Runtime。

### 人工黑屏与性能测试（全部待用户执行）
1. 关闭原型后首次启动，观察从执行命令到窗口可见、页面显示及桥接就绪，有无白屏/黑屏/冻结；不把依赖检查耗时作为窗口启动速度。
2. 点击通信按钮10次，检查返回结果及每次RTT。关闭后再启动5次，分别记录首次/后续运行及是否卡顿，勿把窗口整个存活时间作为启动耗时。
3. 连续最小化/恢复10次、最大化/还原10次；另最小化停留30秒后恢复。每次确认占位区与文字完整，立即点击通信按钮，记录是否响应。
4. 若黑屏，记录发生动作、持续时间、是否自行恢复、窗口尺寸及显示缩放；恢复后点击“记录人工观察点”。观察点只辅助对齐时间，不代表自动通过。
5. 用系统关闭按钮退出，确认Python进程结束；查看日志是否有closed/gui_loop_returned。可在任务管理器观察该Python及WebView2子进程，确认本轮无服务监听，不以UI存在证明无服务。

日志目录D:\code\Signing\.local-tests\webview-logs，每次运行独立JSONL（--check也产生日志）。查看最近文件：
```powershell
Get-ChildItem -LiteralPath 'D:\code\Signing\.local-tests\webview-logs' -Filter '*.jsonl' | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content
```
指标解释：since_entry_ms从main.py首个perf_counter开始，不包含进程创建、Python解释器初始化及此前time导入；webview_imported.duration_ms为导入耗时；window_object_created仅创建Python窗口对象；gui_loop_requested到window_shown/loaded是框架初始化/事件代理，不是系统首帧绘制。js_ready中的script_start_ms/bridge_ready_ms以浏览器performance时钟记录，script_to_bridge_ms是脚本到桥接就绪间隔，不是纯JS执行CPU时间；不能与Python时钟相减。bridge_rtt为JS单调时钟测量的JS→Python→JS往返（含调度），不包含随后写回测量日志的调用。无法直接测量系统真实首帧/像素黑屏/解释器启动耗时，不生成伪造数值。日志I/O会有少量观测开销。


## 当前黑色签名应用（本轮）
用户已人工确认上一版窗口启动、最小化恢复、缩放和通信基本正常；正式采用PyWebView，不再计划Tkinter。新接入的业务交互与视觉效果仍待人工验收。

安装/更新与运行：
```powershell
Set-Location -LiteralPath 'D:\code\Signing'
& 'D:\code\Signing\.venv\Scripts\python.exe' -m pip install -r 'D:\code\Signing\app\requirements.txt'
& 'D:\code\Signing\.venv\Scripts\python.exe' 'D:\code\Signing\app\main.py' --check
& 'D:\code\Signing\.venv\Scripts\python.exe' 'D:\code\Signing\app\main.py'
```
界面选择图片，或向图片区拖入单张PNG/JPG/JPEG，点击提取。右侧切换棋盘/白底；V2锐化默认关闭。完成后分别点击PNG/GIF导出，选择目标路径；每种格式单独显示结果。默认均裁剪透明留白后等比缩放到42px高；PNG保留连续Alpha，GIF128阈值单级透明，淡笔可能失败且不写入目标文件。裁剪只按非零Alpha包围盒，不裁切非零笔画。缩小后的可读性需人工确认。
新导入与重新处理清空旧结果，错误不沿用旧图。取消选择后需重新导入。导出校验后才替换目标；选择文件方式禁止覆盖原路径，拖入方式因没有完整路径会保守禁止与源文件同名导出。导入限制30MB/2000万像素；EXIF方向归正，透明输入先合成白纸。预览仅缩小副本，不修改原始文件。
正式业务代码：app/algorithm.py复用V1原尺寸核心；app/sharpen.py复用V2；app/processing.py负责校验、会话与导出；app/window.py负责原生对话框、桥接互斥和诊断。桥接函数由PyWebView工作线程运行，JS使用Promise等待，处理时禁用重复操作；无HTTP或CDN，图片预览使用内存data URL。窗口层不记录图片内容。
本轮需手测：中文路径选择与拖拽、灰白底真实图、两种背景、新图清空、坏图/空白图、淡灰GIF报错后PNG仍可导出、处理时窗口响应、对话框取消及覆盖行为。原型诊断按钮仍保留。
自动检查：
```powershell
& 'D:\code\Signing\.venv\Scripts\python.exe' -m unittest discover -s 'D:\code\Signing\tests' -v
```
