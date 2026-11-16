## 浅彩识别与蓝章亮度
分类纳入更浅的连贯彩色笔迹，忽略中性行带对彩色行带计数的影响；诊断含彩色行带、连通主体、混合判断等。蓝色主导像素改为保留输入白底外观的RGB/Alpha分解，红色路径不变。手动类型仍可兜底；真实章图请检查自动结果、内部文字、细线、透明边缘与白底预览。

## 彩色识别容错与手动类型
识别不确定时可在导入区域选择黑色签名或彩色印章，再提取；类型变化会清旧结果。新导入/重新框选恢复自动识别。有限灰黑横线允许与连贯彩色主体共存；灰底彩色分离不使用黑签算法。手动类型不绕过空白/噪声和输出有效性检查。请用实际蓝椭圆、灰底红章检查自动结果、透明背景、细笔和PNG/GIF；识别通过不代表视觉合格。

## 自动识别与彩色处理
点击或拖入后分析有效墨迹，显示黑色签名/彩色印章/无法可靠判断；框选确认会重新识别。不确定时禁止提取并提示先框选。黑签沿用V1和增强，彩色走独立白纸保色分离、不使用黑签增强；PNG连续Alpha，GIF使用保色调色板但仍有单级透明和量化限制。尺寸预设不自动改变，请按实际需要选择。仅启发式识别，彩色图形可能误认印章，非白背景/浅彩真实效果需验证。

## 当前笔迹增强入口
笔迹增强已简化为默认勾选复选框：勾选使用既有标准参数，取消关闭增强（覆盖下方历史四档UI说明）。切换后需重新提取，预览与PNG/GIF使用同一结果。请手测勾选/取消、提取/导出、控件悬停和键盘焦点；独立框选窗口保持原状。运行入口不变。

## 笔迹增强（覆盖历史自然锐化开关）
原位置提供关闭、轻度、标准、强力，默认标准。改变档位后重新点击提取；当前结果统一用于透明预览和PNG/GIF。关闭保持原V1；增强连续Alpha，不恢复已删笔迹。强力可能加深已有背景残留，真实图需人工判断。对比运行 `.venv/Scripts/python.exe experiments/ink_enhancement_compare.py`，结果仅在.local-tests/ink-enhancement，含四档原生/缩小PNG和GIF及comparison.png。

## 当前窗口与表单规则
框选弹窗相对Signing主窗口当前中心定位，超出当前工作区时修正位置；覆盖下方历史并排策略。尺寸/导出面板统一圆角表单，顺序与功能保持。手测：移动主窗后关闭重开弹窗、靠屏幕边缘及副屏打开；检查表单焦点、比例锁、尺寸输入与窄窗换行。

## 框选窗口定位
窗口优先放Signing右侧，放不下尝试左侧，再不足则在Signing所在显示器工作区居中；不会移动主窗口，不永久置顶。请手测主窗靠左/靠右/居中、任务栏和负坐标副屏、100%/150%缩放、重复打开与确认取消，检查完整可见和焦点。

## 框选窗口快捷键
默认900×650并按当前屏幕工作区限幅居中。空格+左键拖动移动画布，Ctrl+滚轮围绕鼠标缩放；适应窗口重新居中且保留选框。顶部工具及底部确认/取消固定，底部显示提示。请手测缩放/平移后选区裁切位置、失焦和松空格后的框选恢复、窗口缩小后底部按钮可见；尤其检查多屏及Windows高DPI。运行入口不变。

## 独立框选签名区域
导入图片后点击“图片导入”右侧“框选区域”，在独立窗口拖动新建矩形，框内拖动移动，四角调整。支持缩放、适应窗口和重置选框；宽高至少4个原图像素。确认后左侧显示裁切，再点“提取黑色签名”。取消或关闭不改变结果；重新框选始终基于最初导入原图。
手测：导入整页合成A4，检查缩放/窗口尺寸变化后的四角定位、重选不同区域、取消保留旧结果、确认清空结果、新图清空选区，并验证PNG/GIF尺寸与原文件不变。启动入口仍为 `.venv/Scripts/python.exe app/main.py`。仅单矩形，无旋转/OCR/多选。

## GIF浅笔导出更新
GIF使用自适应Alpha门限和灰度调色板，避免浅笔全部删除或统一变黑；尺寸不变。重读覆盖率或墨量不足90%明确失败并保留原目标。GIF单级透明在深色背景无法等同PNG连续Alpha，复杂噪声及真实图仍需人工验收。合成对比：`.venv/Scripts/python.exe experiments/gif_alpha_compare.py`，输出仅在.local-tests/gif-alpha。

## 独立背景优先对照实验
运行 `.venv/Scripts/python.exe experiments/background_first.py` 生成合成案例；加 `--input 本地图片路径` 对照指定图片。输出默认 `.local-tests/background-first`，仅允许写入.local-tests；同名输出会覆盖。原生PNG与统一148×74全视野PNG/GIF、白/深底预览和JSON均保留；不模拟正式裁剪导出，不替代V1，不等同Photoshop颜色范围。真实样本结果需人工检查。

## 导出尺寸与DPI说明（2026-11-15）
PNG保存并重读校验DPI；GIF无可靠DPI元数据，以实际像素为准，其他软件显示的72 DPI不代表像素变化。厘米按所选DPI换算并四舍五入至整数像素：42px在96 DPI为1.11125cm，固定厘米存在微小取整误差。修改外部软件分辨率时请检查是否启用重采样。启动和测试入口沿用下文。

# 最新界面及规格（覆盖下方历史规则）
手写签名：**高1.1cm、宽度按有效内容比例自适应**；另提供高0.9cm快捷项。96DPI对应高42px、34px。法人1.6×1.6cm、建造师4×2.8cm、公章4×4cm，cm/px、DPI及自定义保留。固定画布始终等比居中留白，不拉伸。
顶部尺寸面板 → 左侧点击/拖入图片区与文件名、右侧透明结果 → 锐化/白底选项 → 提取/导出及状态。点击左侧可更换图片，更换会清除旧结果与导出状态。诊断折叠保留；尺寸最多显示3位小数，内部计算保留精度。常见窗口紧凑布局待人工测试，未承诺所有Windows缩放比例无滚动。
运行：
```powershell
Set-Location -LiteralPath 'D:\code\Signing'
& 'D:\code\Signing\.venv\Scripts\python.exe' 'D:\code\Signing\app\main.py'
```

## 历史说明（以顶部最新规则为准）
# 当前导出规则（本轮生效）
用户已人工确认上一轮黑签V1导入、预览及PNG/GIF基本可用。当前新增图像尺寸面板和统一“导出文件”，新交互待人工验收；历史说明中的“高42px”及双导出按钮已被下述规则替代。
- 手写签名默认宽1.1cm，高按提取后非零Alpha内容比例自适应。96DPI宽42px，**不再固定高42px**。
- 法人章1.6×1.6cm、建造师章4×2.8cm、公章4×4cm，仅为尺寸模板，不增加印章算法。
- 自定义宽高，支持cm/px切换和DPI；默认96DPI，范围1–2400。保持比例默认开启，修改任一边按签名内容比例推算另一边；选择固定双尺寸规格时先采用指定画布，只有编辑边长才触发联动。
- cm按px=cm/2.54×DPI，使用Decimal ROUND_HALF_UP（0.5向上）；px输入也按此规则取整。96DPI三个固定规格分别60×60、151×106、151×151px。
- 始终按非零Alpha包围盒取内容，等比缩放后透明画布居中；解锁比例只改变画布，不拉伸。预览仍显示原尺寸提取结果，面板单独显示最终像素。改尺寸不重新提取。
- 单位切换换算当前边长；cm模式修改DPI保留cm值并重算px，px模式修改DPI保留px值（改变物理解释）。单边1–10000px、总量不超过2000万像素，防止误输入分配超大图像。
- PNG连续Alpha并写入DPI，GIF单级透明不能可靠保存物理DPI；GIF全透明/无透明背景仍拒绝，导出失败不替换已有目标。不覆盖输入图片规则保留。

本地启动：
```powershell
Set-Location -LiteralPath 'D:\code\Signing'
& 'D:\code\Signing\.venv\Scripts\python.exe' 'D:\code\Signing\app\main.py'
```
人工验收：处理一张图后切换签名/三种章尺寸/自定义，检查预计px；编辑宽高、切换单位和DPI、解锁比例，分别导出PNG/GIF重读尺寸；检查留白居中、细笔画及淡笔GIF失败，确认改设置无需重新处理。

## 先前使用记录（导出规格以本文顶部为准）
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
