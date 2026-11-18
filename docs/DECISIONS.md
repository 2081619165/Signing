## 2026-11-18 诊断安全降级与隐私
复用Diagnostics，不增加服务或进程。文件系统/序列化异常不传播，write_failures与last_error_type留内存并在application_return尽力上报。异常堆栈仅文件basename/行号/函数名，不记录异常文本、客户路径或源码行；浏览器js_error仅记reported。_run记录operation及received/started/completed/cancelled/failed/released，异常类型与堆栈分开。退出新增main_close_cleanup_begin/returned和application_return(退出码/非daemon线程/写日志失败计数)，不宣称记录真正进程退出。框选用户等待仅补closed状态轮询，不引入操作超时。

## 2026-11-18 受约束候选复核
原noise_ok未过时，仅noise<=.035且color_noise<=.025、背景比例/四象限仍通过才生成候选；不改变颜色/Alpha门限。原纸张范围、强笔保留和密度保护继续执行。二次复核联合要求：背景样点Alpha>2泄漏<=1%、外围约3.5%宽边非透明<=2%、候选密度0.5%-50%、最大Alpha>=2组件>=12、存在强笔且保留>=98%。任一不满足回退基线，最终process校验不放宽。所有候选要求连贯主体>=12防散点误接收；纯白正常红蓝保留基线路径。无新增模块和人工固定红蓝RGB。

## 2026-11-18 彩章模型应用与质量提示
processing对彩章统一请求既有背景模型，extract_color默认参数保持兼容，近白正常结果继续基线。拟合样点归一化后的彩度95分位估计color_noise：亮度残差原限仍成立，或在残差<=.035且彩度噪声<=.008时允许有限中性纹理；软Alpha门限/过渡随color_noise调整。强笔保护需相对彩差>max(.03,3*floor)，避免保护色偏背景。候选在纸张样点Alpha>2比例>15%回退，2%至15%附quality_warning并复用现有状态原因展示；现有组件/密度硬校验不放宽。不补画、不统一指定RGB，核心黑签/大图/导出未改。

## 2026-11-18 框选可选、整图工作图缓存
超过20MP只切换压缩源/预览存储策略，不再强制先框选。大图未框选时在process第一次从full范围生成工作图，保留原source/原坐标，whole_work_ready缓存防重复解码；重新导入重置缓存标记，框选继续复用源坐标裁切。工作图预算、文件/源图解码保护不变。直接彩章仍使用既有非local基线，框选才启用local，颜色规则不变。释放Pillow临时对象/预览串，不扩大UI/线程架构或使用强制结束进程。

## 2026-11-17 分离原图、预览、选区和算法工作图
原图保留完整尺寸/压缩源，框选预览<=1600边，主预览<=1200×900；选区保存原图floor/ceil坐标，不再受400万面积限制。working_image只等比缩小，算法输入<=200万像素且最长边<=3200；LargeSource先按原图裁切再缩工作图，转换RGB前缩小以减少副本。普通图片同样限制算法输入，小图像素保持不变。结果基于工作图，预览/旋转/原有尺寸导出共用；不把结果伪称原分辨率提取。不改颜色/黑签核心规则。
仍保留：30MiB文件（拖入Base64桥接42MiB字符预检）、50MP源尺寸及16字节/像素<=800MiB解码估算、Pillow异常格式/图像保护、至少4×4选框及越界检查；>20MP仍须框选（可全选），此为流程分界而非选区拒绝。导出1至10000px单边/20MP总量及DPI规则不变。捕获内存不足时不提交半状态。

## 2026-11-17 大图导入与原图预览分离
在现有processing.py复用预览辅助并新增轻量LargeSource对象，不新增模块。小图保留现有原图流程；大图original为小预览、full为压缩源/逻辑尺寸/预览，crop模块依然读取full.size计算原图坐标并通过resize拿缓存预览。确认才ImageOps.exif_transpose原图并裁切、白底合成选区，不对预览提取；新图清状态。大图禁止直接process，即使手动类型也需框选。分类仅受限预览，不改classify/extract函数。点击导入先stat文件大小再read_bytes。

## 2026-11-17 框选入口与全链路日志
复用Diagnostics统一添加PID和线程名/ID/daemon；启动增加固定诊断版本，不引入日志模块。输入文件只记录字节数，不记路径/名称/内容；原文件大小由Session.load保存，框选使用同源大小。前端日志异步不阻塞原调用；传入随机请求ID与crop内部贯通。原生创建返回后记录native/shown/loaded状态，before_show事件尽力采集；这是可观察初始化标志，不冒充WebView2底层成功证明。

## 2026-11-17 框选生命周期与退出清理
crop请求持有取消回调，主窗closing立即设置shutdown并唤醒ready/done，后续打开被拒；prepare为daemon并在创建前后检查aborted。清理由Form.Close/BeginInvoke正常UI消息执行，不join UI/桥接线程、不os._exit或TerminateProcess。关闭后移除active/requests并释放互斥；gui_loop_returned追加存活线程清单诊断。创建后检查events.loaded/closed.is_set补偿订阅竞态，loaded幂等。

## 2026-11-17 整页大图框选修复
只在app/crop复用既有桥接与日志：预览最长边1600，页面stage仍用full原图尺寸，因此现有坐标映射不变；原图不重新解码、不做全图PNG编码、不降提取分辨率。原生创建按PyWebView要求交其GUI线程，prepare后台负责缩图/编码，45秒等待覆盖准备/页面/图片解码和显示返回。失败清理异步、晚到创建检查aborted，互斥防并发；正常显示后用户选区不限操作时长。

## 2026-11-17 彩章失败结构化诊断
复用Diagnostics.record输出color_diagnostic，每次process有随机request关联；不写路径、坐标、原图、像素矩阵或印章内容，仅汇总统计/背景均值与阈值结果。extract_color report补基线/候选/最终Alpha及阶段耗时，process在抛异常前写校验结果。实验脚本增加--input本地对照，只允许固定.local-tests输出，不自动拿历史样本当当前故障样本。

## 2026-11-17 彩章局部背景分离
现有algorithm.py保留旧函数extract_color_baseline；新增包装只local=True（Session.crop_box非空）启用，约12000有界采样二次背景曲面迭代剔除墨迹。背景样点需覆盖四象限且多数、残差/亮度可信；近白正常基线、强笔迹损失回退。按估计纸张归一化后以噪声相对软权重生成连续Alpha，不补画。彩章校验由单个Alpha>=8且面积8，改Alpha>=2多个面积>=2组件合计>=12；基线密度上限65%保留，可信局部结果85%。不取消随机噪声/空白保护。

## 2026-11-16 SealKit品牌与发布准备
保留Signing仓库/路径及现有架构。原创几何图标由tools/branding/generate_icon.py统一源生成SVG/PNG/多尺寸ICO，不依赖第三方商标。页面图标内联data URL，窗口用webview.start(icon)，AppUserModelID为SealKit.Desktop。无既有打包配置，新增packaging/SealKit.spec白名单收集资源及WinForms/WebView/pythonnet运行文件，console=False/单文件。冻结运行日志迁移LOCALAPPDATA/SealKit/logs；资源仍按模块__file__读取。

## 2026-11-16 旋转移至透明结果
覆盖上一轮原图旋转设计：旋转仅在去背景与可选增强后执行，透明RGBA BICUBIC expand填充透明；Session保留base_result且每次从母版计算，result作为预览/导出唯一结果。框选窗口不再持有角度。旋转异步串行，只显示最新角度，更新过程中禁止导出并使旧预计尺寸请求失效。

## 2026-11-16 框选窗口旋转矫正
复用crop桥接新增rotate预览与confirm(box,angle)；Python预览/最终均Pillow BICUBIC+expand白底，正角逆时针。选区坐标属于扩边后的旋转原图。每次从full原图旋转防累计采样；Session.rotation只在确认裁切成功后提交，重开恢复已确认角度/框，新导入归零。角度调整重置选框、适应窗口，平移/缩放逻辑不改。

## 2026-11-16 浅彩识别与蓝色亮度保留
沿用单一extract_color，蓝色主导(B>R+.03且B>G+.03)保留原RGB再做白底分解，红章原归一化不变。不直接增加不透明度或指定深蓝，不扩张支持范围。分类彩色证据门限S>=32、通道差>=10；彩色自身bands<=12、比例>=50%或有限横线补充证据，继续保留连通/密度/整页限制及手动兜底。

## 2026-11-16 彩色识别容错与手动类型
补充彩色连贯主体证据（至少16彩色像素、最大连通域>=12、彩色密度<50%），保留彩色纵向整页/行带保护。彩色比例>=65%或至多两条中性长横线可自动判彩章；不删除所有安全判断。手动类型仅选择路由，不跳过空白/噪声检查和彩色提取后主体/背景残留检查。彩色RGB先按最大通道归一化以抵消中性灰纸，再反算前景和连续Alpha；黑签extract/增强、GIF/DPI逻辑不动。

## 2026-11-16 自动识别与彩色处理适配
在现有algorithm.py新增classify/extract_color，不改extract。有效区域由局部背景差和饱和墨迹联合决定；彩色比例>=90%为color_seal、<=3%为black_signature，其余uncertain；有效像素不足、密度过高、纵向整页、多连通块/多行拒绝。process重新识别兜底，彩色不经过黑签V1/增强。白纸模型Alpha=1-min(RGB)，按Alpha反算前景RGB；彩度门限仅去中性纸张。GIF复用原Alpha门限/质量检查，彩色才用255色量化并预留0透明索引，黑签灰度调色板不变。不自动改业务尺寸预设。

## 2026-11-16 增强开关与控件美化
当前前端仅提供笔迹增强复选框，默认checked；显式发送standard/off字符串，复用既有参数与Session.result，覆盖历史四档前端入口。Python四档能力不变以保留实验与兼容性。美化复用现有CSS与原生控件，不增加组件或依赖。

## 2026-11-16 四档笔迹增强
保留legacy_sharpen供实验对照，正式sharpen使用四档连续Alpha映射1-(1-a)^(1+gain*confidence)，gain=0/.6/1.2/2，confidence=min(Alpha/32,1)。不做二值化、膨胀或额外边缘锐化；非零范围严格保持，小于等于3像素孤立连通域不增强。关闭逐像素保持V1。布尔旧调用False/True兼容关闭/标准；桥接不再bool化字符串。增强在V1之后且尺寸缩放之前执行，GIF逻辑不改。

## 2026-11-16 主窗口居中与表单样式
当前定位以main.Bounds中心减弹窗半宽高，随后按同坐标系WorkingArea夹紧；取代此前优先并排策略。原有900×650默认尺寸换算、工作区限幅、非永久置顶激活均保留。表单外观只作用于export-settings，不改JS/HTML业务顺序。

## 2026-11-16 框选窗口定位与激活
最小Windows适配集中app/crop/placement.py，读取主窗口native.Bounds、Screen.FromControl(...).WorkingArea，并在UI线程设置弹窗原生Bounds；默认900×650及16间距仅一次按主窗口DeviceDpi换算。隐藏创建后loaded定位显示，避免初次错误位置闪现；Show/BringToFront/Activate且on_top=False。会话锁继续阻止重复创建，active引用支持已有窗口激活并在closed清理。

## 2026-11-16 框选窗口交互优化
继续使用现有crop模块。显示坐标由scale和offsetX/Y共同决定，选区仍存原图坐标；鼠标缩放以锚点不变反算偏移，适应窗口仅重算比例与居中位置。画布overflow hidden，由Space抓手平移；工具栏和底栏flex-shrink:0。Windows现有WinForms依赖提供鼠标所在屏幕WorkingArea，不引入依赖。

## 2026-11-16 独立框选窗口
框选作为app/crop独立窗口/受限桥接，主桥接在会话锁内等待弹窗关闭，主界面busy禁用业务操作。保存EXIF归正及白底合成后的完整RGB原图；单独工作副本用于裁切及V1。浮点原图坐标左上floor、右下ceil，边界及最小尺寸校验后才提交。取消/关闭不触碰原会话。全图快照通过内联data URL，无新增HTTP服务或依赖。

## 2026-11-15 GIF浅笔修复（覆盖历史固定128规则）
GIF采用灰度不透明索引表达原黑RGB+Alpha在白底的灰度，0索引透明；避免所有保留像素变黑。门限为有效Alpha>=4的95分位×20%，限制4至32；必要时逐级降低至4以争取95%参考覆盖和墨量。最终重读硬门槛90%。不膨胀、不连线、不重复采样。低Alpha及噪点仍有歧义，灰度GIF深底外观不等同连续Alpha PNG。

## 2026-11-15 黑签笔画专项实验
背景优先仅独立实验：所有RGB通道接近白才去除，20至90暗度软过渡，0.3px高斯柔化Alpha，无连通域删除；Fuzziness70仅作为实验过渡宽度启发，不等同Photoshop选择算法，亦非JSX复刻。保留原RGB，与V1黑RGB/相对Alpha不同；视觉须合成背景比较。统一全视野缩放排除不同裁剪干扰；不改正式算法。

## 2026-11-15 导出准确性
沿用Decimal HALF_UP及单次等比缩放。GIF以像素为准，不通过二次采样模拟DPI；PNG pHYs整数像素/米允许0.0128 DPI量化误差，重读验证后才替换目标。

## 本轮：规格纠正与紧凑布局
本轮覆盖此前宽1.1cm错误规则：签名高1.1cm或0.9cm，宽按有效内容比例；后端默认缺省高度1.1cm，支持仅传height或width推算另一边。固定画布等比适配透明居中，DPI96默认、Decimal HALF_UP换算不变。前端显示尺寸最多3位小数，内部Map保留JS数值精度，预计与导出使用同份内部值。左侧整块button作为导入/更换入口及拖放目标，保留键盘操作；诊断默认折叠，预览高度clamp随视口调整，不隐藏必需操作或禁止滚动。

## 先前记录
## 当前生效导出规格（覆盖历史固定高度）
签名宽1.1cm、高按非零Alpha内容比例；法人1.6×1.6cm、建造师4×2.8cm、公章4×4cm、自定义。默认96DPI可改1–2400。backend Session.dimensions使用Decimal和ROUND_HALF_UP统一换算，预计与导出共用，前端不自行断定最终px。px单位边长也按同规则取整；超限或小于1px拒绝。
双固定宽高含自定义均为画布，ImageOps.contain等比适配、透明居中；解锁比例不授权变形。比例锁用于用户改边长时按内容比例联动，固定预设初始不被锁覆盖。单位切换保持物理尺寸，DPI修改时保留当前单位输入值。统一按钮按选定PNG/GIF保存，原有原子替换/重读校验复用，PNG写所选DPI。
只扩展现有processing.py和桥接/前端，无新增算法或业务模块。章预设仅尺寸，不代表能处理红蓝章。

## 历史记录
## 本轮生效：正式黑签处理
不采用Tkinter；用户已验证PyWebView原型。按现有app目录最小扩展而不另建包树。V1核心从实验版适配为extract(image)->原尺寸RGBA，算法操作不变，去掉磁盘与400×200实验画布；V2按原函数保留，默认关闭。许可证随正式模块保存。
PNG/GIF统一42px高并按内容比例定宽。连续Alpha不等于颜色强制加黑：复用V1黑RGB+相对墨量Alpha，不将Alpha硬二值化用于PNG。GIF有损128阈值不改为自动加黑，全透明明确失败；重读合格后原子替换目标。临时文件在目标目录并finally清理。
选择文件走原生对话框，拖拽用FileReader传内容，无需HTTP或浏览器完整路径。业务会话以非阻塞锁拒绝重入，PyWebView原有后台桥接线程执行处理，不使用UI线程。原图/结果仅保留在内存，数据URL只用于预览，无真实图片写入仓库。状态由前端busy和后端互斥共同保护。

## 先前记录
# 本轮生效决策：PyWebView原型
用户明确选择覆盖此前Tkinter建议。采用Python+PyWebView+静态HTML/CSS/JS；固定edgechromium，检测WebView2注册表与.NET release，记录实际renderer，发现非edgechromium关闭，不接受静默MSHTML成功。仅最小原型，不改变算法分层规划。
Windows官方后端：edgechromium、已弃用mshtml、可选CEF；另可选Qt需额外依赖，本轮不安装。6.2.1实际winforms源码仍可能在条件不满足时选MSHTML，因此增加先决检查及实际后端记录。CEF/Qt不作为本轮降级方案。
资源由Python读取并注入HTML内联，create_window(html=...)，start(http_server=False)，不用相对文件URL触发自动HTTP服务。保留原生标题栏，避免动画与透明合成。诊断只开放ping及固定事件上报，不开放算法/文件系统接口。
依据：https://pywebview.flowrl.com/guide/web_engine.html 、https://pywebview.flowrl.com/api/ 、https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution 。系统组件仍需用户安装，注册表存在不是渲染成功保证。

## 历史架构建议（Tkinter部分已被本轮替代）
# 技术决策与整合规划
2026-11-13：建议采用Python + OpenCV/NumPy/Pillow；GUI优先Tkinter/ttk，无Web框架及后台服务。Tkinter是Python的Tcl/Tk接口，分发时仍需包含对应运行库，不能宣称零体积。依据：https://docs.python.org/3/library/tkinter.html 。本轮不安装或创建GUI，不承诺EXE尺寸。

## 拟定正式结构（尚未创建）
```text
src/signing/
  algorithms/signature.py  # 迁移复用V1原尺寸提取
  algorithms/sharpen.py    # 复用V2可选能力，不继续优化
  algorithms/seal.py       # 必要红章算法适配；蓝章待验证后增加
  pipeline.py              # 读取、分类、调度、错误与结果状态
  export.py                # 统一尺寸、等比缩放、PNG/GIF和重读验证
  gui.py                   # Tkinter/ttk单窗口与后台任务调度
```
避免为每个辅助函数拆文件。experiments保留原算法对照和回归，不整包复制上游。正式包不得依赖experiments或.local-tests。

算法层接收图像、返回原尺寸RGBA和质量信息，不写业务文件；业务层统一process请求（路径、auto/黑签/红章/蓝章、业务规格、可选锐化）和结果（类型/置信度、未锐化及最终RGBA、警告、各阶段状态）。保留现有extract接口作实验适配，不直接改变其默认行为。导出层独立处理文件与尺寸；锐化模块内export_gif后续迁移复用，避免重写。

自动分类先用色彩证据判红/蓝/中性；低置信或混合色不猜测，允许用户选择。印章颜色不能自动确定法人/建造师/公章业务规格，该规格由用户选择。未实现类型明确提示不支持。

业务尺寸保留：法人60×60、建造师151×106、公章151×151；签字默认高42px宽自适应，34px备选以后配置。96DPI仅物理换算；始终等比缩放+透明留白，不拉伸。PNG保留连续Alpha，GIF单级透明有损；全透明、无透明或尺寸错误不可报告导出成功。不得用补画或无条件加黑解决失败。

GUI建议：单图打开、自动/手动类型、业务规格、锐化开关、原图/结果白底与棋盘格预览、PNG/GIF保存；不做复杂参数面板。处理任务移出UI线程，主线程刷新控件，防重复任务，错误可见；预览独立于算法透明数据。先完成接口与失败状态，再接界面，最后另轮验证打包。

## 许可证与版本
show7固定f7da5df17bda46a56bf588baa78843baa5b8779a；leopens固定4e571b3f25cc8431756476e96976c392abda398e。两者MIT允许复用及分发，实质代码须保留版权和许可；show7声明在experiments/licenses。正式分发前补THIRD-PARTY notices及依赖许可清单，Signing整体许可证尚未决定。leopens仅实验，不为它把SciPy带入正式运行层。

V1局部背景估计及连续Alpha保留；V2为经验筛选+轻度Alpha反遮罩，以五级像素集合不变和墨量变化<=1%回退。保留未锐化版本和开关，不宣称恢复不存在的细节。
## 2026-11-17 框选验证与提交顺序
Session.validate_crop统一边界/尺寸/安全预算检查，子窗confirm通过桥接回调先检查再关闭，Session.crop提交前再次检查。保留原图坐标和400万像素选区上限。先生成裁切图、预览与分类，再一次提交original/crop_box/requires_crop/result等状态；不靠移除process安全检查解决失败。响应增加requires_crop，提交日志记录实际尺寸和状态。
