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
