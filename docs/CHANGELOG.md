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
