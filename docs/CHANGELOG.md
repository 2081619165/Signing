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
