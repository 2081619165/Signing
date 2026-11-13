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
