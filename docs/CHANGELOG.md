## 2026-11-19 灰底暗红印章贴边

修复灰底暗红章贴边圆环触发外围残留误判，增加本地真实样本回归。

## 2026-11-19 旋转预览比例

修复旋转斜角时印章预览自动缩小。

## 2026-11-19 Codex 全局设计技能

将两个设计技能安装到当前账户的 .codex/skills，并将全局 ui-ux-pro-max 的命令示例改为全局路径。

## 2026-11-19 前端设计技能

加入 UI UX Pro Max 与 Anthropic Frontend Design 技能及配套资源，通过临时 Git 克隆安装。

## 2026-11-19 透明结果旋转范围

扩大旋转范围并加入角度输入和四分之一转快捷键，补充边界、连续旋转及导出回归。

## 2026-11-19 橡皮擦平移快捷键

增加空格抓手、纵向与横向滚轮平移；「适应」重置滚动位置。

## 2026-11-19 内嵌透明结果橡皮擦

将独立橡皮擦迁入右侧预览，增加可视笔刷、滚轮缩放与中键平移，清理独立编辑窗资源和打包条目。

## 2026-11-19 新增透明结果橡皮擦

新增 app/eraser 窗口资源。主界面加入入口，处理会话接收擦除掩码，复用窗口桥接、诊断和关闭清理，补齐打包资源声明和自动回归。

## 2026-11-18 隐藏开发诊断展示
仅修改app/static/index.html：运行诊断details增加hidden属性，不删除控件、不改JS/Python/样式或底层架构。同步更新PROGRESS、CHECK_REPORT及本日志；未提交或推送。

## 2026-11-18 诊断最小加固
仅window.py日志安全降级/操作标签/隐私堆栈/退出状态/诊断版本，crop/__init__.py用户等待补closed状态检查，tests/test_crop_placement.py补日志及关闭回调丢失回归；README及相关docs同步。无新增文件，无算法/GUI/导出修改，无提交推送打包。

## 2026-11-18 真实红章候选复核修复
仅algorithm.py新增中等噪声候选联合复核与连贯主体保护；tests/test_processing.py新增纹理拒绝和环境变量传入真实图回归（未设置跳过，不依赖客户图片提交）；既有experiments/color_background_compare.py本地输入增加三种背景比较及Session完整流程报告。README及docs同步。无新文件，无GUI/处理机制/导出修改，不提交推送打包。

## 2026-11-18 彩章偏色纸与纹理改善
仅修改algorithm.py背景相对彩噪估计/软Alpha/强笔保护/纸张泄漏报告，processing.py彩章启用既有模型及现有质量提示；tests增加粉底红蓝/浅线/空白负例，既有experiments/color_background_compare.py补纹理案例；README及docs同步。无新增文件，不改大图/框选/GUI布局/导出，不提交推送打包。

## 2026-11-18 取消大图强制框选
本轮修改processing.py整图工作图缓存/日志、导入分类恢复及Pillow临时对象释放；window.py导入取消时清旧base_result；crop/__init__.py关闭后清预览串；tests/test_processing.py更新直接提取/缓存及旧状态预期；README和相关docs同步。无新增文件，不改颜色核心/GUI布局/导出，无提交推送打包。

## 2026-11-17 高分辨率完整选区处理
本轮仅修改processing.py新增working_image、去除4MP选区硬拒、算法使用受控输入、报告原图选区/工作尺寸及裁切内存错误；window.py补MemoryError明确反馈及尺寸日志；tests/test_processing.py调整旧4MP预期并新增2493万像素完整链路/内存回归；README和5份docs同步。无新增文件。其余Git工作区既有改动保留；未改GUI、算法核心、导出规则，无提交推送或打包。

## 2026-11-17 大图导入与原图预览分离
本轮增量仅processing.py预览/压缩源分离、解码预算与大图选区保护，window.py选文件大小预检查，tests/test_processing.py大图/方向/预算回归，README及5份docs。无新增文件；既有experiments/color_background_compare.py未跟踪状态不属于本轮新增。其余工作区既有改动保留，算法/GUI/导出未改。

## 2026-11-17 框选入口与全链路日志
static/main.js仅框选入口添加异步结构化诊断/请求编号；window.py补Python入口/返回/异常、诊断版本与统一线程PID；crop模块补初始化/取消/确认/异常和WinForms显示日志；processing.py仅保存输入字节数供诊断；tests补入口回归，README/docs补判读。不改算法、布局、导出或打包，无提交推送。

## 2026-11-17 框选生命周期与退出清理
crop/__init__.py增加close_native/shutdown、请求登记和取消、事件状态补偿、正常清理及结束日志；window.py主窗closing和事件循环返回调用清理并记录线程清单；tests新增主窗关闭生命周期回归，更新README及docs。无算法/GUI布局/导出改动，无Git提交推送。

## 2026-11-17 整页大图框选修复
crop/__init__.py新增受限预览、分块API、后台准备、请求/阶段日志、45秒超时与并发保护；crop/main.js加载前禁确认、桥接取预览、解码事件及失败提示；window.py传现有Diagnostics；test_crop_placement.py补预览映射与失败恢复测试。更新README/docs。不改彩章/黑签/识别/旋转/导出/尺寸/GUI布局，不提交推送。

## 2026-11-17 彩章失败结构化诊断
algorithm.py细化报告与每个回退原因、Alpha过滤和背景可信统计；processing.py增加可选diagnostic回调、分类/路由/提取/校验/成功日志；window.py接现有本地日志。experiment现有脚本补--input对照，tests新增日志回归，更新README/docs。无GUI/黑签/导出/尺寸修改，无提交推送。

## 2026-11-17 彩章局部背景分离
algorithm.py保留彩章基线并增加保守局部背景包装，processing.py仅框选彩章启用新分支并调整相关有效性校验、返回color_report。新增experiments/color_background_compare.py合成对照及tests回归，更新README/docs。无GUI/识别/黑签/增强/旋转/导出/尺寸/DPI/导入上限修改，无Git提交推送。

## 2026-11-16 EXE配置复核（未打包）
本轮仅补充正式EXE准备检查证据与打包说明，复用现有spec，不改界面/算法/功能。未运行PyInstaller、未提交推送。

## 2026-11-16 SealKit品牌与发布准备
主窗口及HTML品牌改SealKit/印迹与统一副标题；CSS品牌收尾和控件细节；main.py说明及window.py图标/AppUserModelID/冻结日志路径适配。新增app/assets原创SVG/PNG/ICO、tools/branding/generate_icon.py、packaging/SealKit.spec与requirements-build.txt。README补打包命令及边界。未改算法/GIF、未打包/提交/推送。

## 2026-11-16 旋转移至透明结果
撤回crop前后端旋转控件/接口，恢复原图裁切；processing.py改为base_result透明母版和rotate_result；window.py新增结果旋转桥接；主界面增加折叠角度控件及串行请求，更新测试和文档。未改识别、提取算法、尺寸/DPI或导出规则，无提交推送打包。

## 2026-11-16 框选窗口旋转矫正
修改app/crop HTML/JS添加角度控件及异步预览，crop桥接增加原图旋转预览和角度提交；processing.py增加rotated与旋转后crop，window.py传递/重置角度；tests新增旋转回归，更新README及docs。未改核心提取、尺寸/DPI、PNG/GIF导出，无提交推送/EXE。

## 2026-11-16 浅彩识别与蓝色亮度保留
仅修改app/algorithm.py浅彩分类证据、彩色行带/诊断及蓝色原RGB透明分解；tests/test_processing.py增加回归；更新README及相关docs。无黑签/增强/框选/尺寸/导出改动，无推送或EXE。

## 2026-11-16 彩色识别容错与手动类型
修改algorithm.py彩色主体判据/诊断数据及灰底归一化；processing.py增加手动类型和提取有效性保护；window.py透传类型；static HTML/JS增加手动类型选择和状态失效；更新回归及README/docs。未改黑签提取、增强、GIF/PNG导出或尺寸规则，无提交推送/EXE。

## 2026-11-16 自动识别与彩色处理适配
修改algorithm.py新增保守类型分析和彩色白纸分离；processing.py导入/裁切返回分类、process安全分支及彩色GIF量化；static/index.html/main.js增加识别提示、按钮文案/禁用和框选更新；tests补分类及保色回归。更新README及文档。不新增依赖/页面/窗口，不改业务尺寸和黑签算法，不提交推送。

## 2026-11-16 增强开关与控件美化
修改app/static/index.html增强下拉框为默认勾选复选框；main.js显式映射standard/off并调整提示；style.css复用表单规则覆盖现有输入/下拉/复选框，统一按钮圆角与悬停/键盘焦点。更新README和相关docs。无新文件/框架、无算法或框选更改，无提交/推送/EXE。

## 2026-11-16 四档笔迹增强
修改sharpen.py保留旧算法并新增四档映射；processing.py默认标准；window.py传递档位而非bool；static/index.html/main.js以同位置下拉框替代勾选并在档位变化时清旧结果要求重新提取。新增对照实验与回归测试，更新文档。V1、GIF透明色、尺寸/DPI未改，无推送或打包。

## 2026-11-16 主窗口居中与表单样式
修改app/crop/placement.py主窗口居中计算、tests/test_crop_placement.py定位预期、app/static/style.css限定范围表单样式。同步README及相关文档。不改提取、鼠标交互、裁切、导出或尺寸/DPI逻辑，无推送/打包。

## 2026-11-16 框选窗口定位与激活
新增app/crop/placement.py及tests/test_crop_placement.py；修改crop/__init__.py为隐藏创建/加载后定位激活及活动窗口管理；window.py传主窗口并优先激活已有弹窗。未改前端内容、交互、裁切、算法或导出。无提交推送或打包。

## 2026-11-16 框选窗口交互优化
修改app/crop/__init__.py工作区尺寸及居中；index.html固定工具栏/底栏与快捷键提示；main.js新增平移、鼠标锚点缩放、默认滚轮拦截和抓手状态清理。更新README及项目文档。算法、导出、DPI、主界面不变，无提交推送和EXE。

## 2026-11-16 独立框选窗口
新增app/crop/__init__.py、index.html、main.js负责独立框选窗口；processing.py新增原图快照/内存裁切，window.py新增select_region桥接；static三文件增加标题同行按钮和确认回调；tests新增裁切回归。更新README和相关文档。未修改算法、锐化、GIF转换或尺寸换算。

## 2026-11-15 GIF浅笔修复（覆盖历史固定128规则）
仅修改app/processing.py GIF转换和重读质量校验；tests/test_processing.py调整淡笔预期并增加回归；新增experiments/gif_alpha_compare.py。更新README及相关文档。V1、锐化、GUI、尺寸/DPI不变，无提交推送或EXE。

## 2026-11-15 黑签笔画专项实验
新增独立背景优先实验脚本及命令入口；生成合成真值、两算法同视野原生/缩小输出和透明度/连通性统计；更新README及专项分析文档。不修改app或现有实验，不推送、不打包。

## 2026-11-15 导出准确性
修改processing.py重读DPI校验和实际尺寸返回；main.js仅更新预计/成功提示文字及格式切换重算；新增尺寸DPI回归测试。V1/V2、布局和依赖不变。

## 本轮：规格纠正与紧凑布局
修改app/processing.py默认高度及单边自动计算；修改static/index.html、style.css、main.js紧凑布局和导入交互、0.9cm项、显示精度；更新tests/test_processing.py默认高度及0.9cm断言；更新README和5份docs。桥接接口复用未改，V1/V2/experiments未改。

## 先前记录
## 本轮修改：图像尺寸与导出面板
修改app/processing.py：统一尺寸计算、可配置DPI及固定透明画布；app/window.py：预计尺寸桥接和导出设置参数；app/static/index.html/main.js/style.css：统一导出按钮和尺寸面板；tests/test_processing.py：新默认宽度及预设/自定义/无效尺寸回归；更新README及5份项目文档。未修改V1/V2或experiments，无依赖变更、无提交推送。

## 历史记录
## 本轮黑签功能整合
新增app/algorithm.py（适配V1内存核心）、sharpen.py（复用V2不含实验导出）、processing.py（校验/会话/PNG-GIF原子导出）、licenses/show7-MIT.txt；修改window.py桥接与依赖检查、static三文件业务交互及requirements图像依赖；新增tests/test_processing.py。更新README、PROGRESS、DECISIONS、BUGS、CHECK_REPORT与CHANGELOG。保留原型诊断及全部experiments，无提交推送。

## 先前记录
## 本轮交付整理
补充最新进度、发布授权及检查说明；按用户要求准备将最小窗口原型与相关文档提交到master并推送origin。不包含样本、日志、虚拟环境或V1/V2修改。

# 本轮修改：最小窗口原型
2026-11-13 新增app/main.py入口、window.py窗口与日志、static/index.html/style.css/main.js静态界面、requirements.txt原型依赖锁定。更新README及PROGRESS、DECISIONS、BUGS、CHECK_REPORT、CHANGELOG。未修改experiments、AGENTS或.gitignore；日志及.venv复用已有忽略目录。未打包/提交/推送。

# 修改日志
## 2026-11-13 本轮审查与规划
仅维护AGENTS、README和docs文档；去除跨文档重复报告，纠正当前输出为gray-v2，标记write_report停用与外部输入实际位置；登记功能矩阵、代码风险、Git状态、拟定四层架构和GUI顺序。未修改Python、未创建正式目录或GUI、未提交/推送。

## 同日 V2
新增signature_sharpen.py，修改compare_gray.py；可选Alpha增强/回退、42px透明GIF、三方预览及检测记录。15项历史分支检查覆盖增强/回退/跳过；淡灰GIF失败未解决，视觉待确认。

## 同日 V1
新增gray_signature.py、compare_gray.py及show7许可；局部背景估计、连续Alpha，取消笔画形态学开闭，保持原算法对照。合成细线/空白负例检查，真实样本无真值。

## 同日 第一阶段
建立规范与文档；固定两个上游提交，源码审查、七类合成输入、8项支持运行、PNG对比及20张GIF，3张淡红GIF全透明。详情见REVIEW.md。
## 2026-11-17 大图确认流程最小修复
修改processing.py拆出共享validate_crop并将预览/分类移到状态提交前；crop/__init__.py确认前校验、拒绝日志；window.py透传验证回调和提交状态日志；tests/test_processing.py新增大图桥接与原子提交回归。同步README及项目文档。未改算法、预览坐标、导出或GUI布局，无新增文件、无提交推送打包。
