## 2026-11-15 导出准确性
已验证：7项unittest通过，包含72/96/300 DPI、74×42实例、PNG连续Alpha和DPI量化容差、GIF单级透明及重读尺寸；compileall通过。新增测试初次因合成图无透明/比例构造错误失败，调整测试夹具后全部通过。未验证：JS实际运行、Photoshop、真实笔画视觉、原生窗口。无当前未解决自动测试失败。前后端静态审查：estimate_size和export_image均传settings并调用Session.dimensions。

## 本轮：规格纠正与紧凑布局
已读取规范及现有前后端、尺寸/导出逻辑。6项unittest通过（默认高42px、0.9cm高34px、固定规格、PNG/GIF尺寸与安全导出、V1一致性等）；compileall通过；HTML ID唯一及JS引用匹配检查通过。未启动窗口，无前端运行/真实分辨率截图或无滚动验收结论。未修改算法或桥接协议，未添加依赖、提交、推送或打包。人工验收：点击左侧/拖入/更换清旧结果，1.1和0.9cm预计与导出对照、比例和单位切换、处理期间禁用，两个分辨率下查看主要操作是否可见。

## 先前记录
## 本轮检查：尺寸与导出
已读规范、README、进度/决策/问题及现有处理/前端/桥接。复用Session.export重读校验、临时文件原子替换与输入保护；新增dimensions作为预计和导出的统一真值。算法与依赖未改。
已验证：6项unittest全部通过；新增覆盖96DPI的60×60/151×106/151×151、300DPI472×331、px半像素向上舍入、PNG/GIF实际尺寸一致、NaN/无穷/零/负/超大输入拒绝、自定义100×200等比留白、尺寸修改不改变内存提取结果；原淡灰GIF失败保护、中文路径、V1一致性及重复请求检查仍通过。compileall通过。
未验证：本轮未启动窗口，JavaScript实际交互、单位切换/比例联动、对话框、缩放后视觉完整性等待用户手动测试。用户已确认的上一轮V1闭环效果与本轮尺寸UI验收分开。无真实图片上传，无算法修改/EXE/推送。

## 历史记录
## 本轮检查：黑签业务整合
实际新增/修改职责见CHANGELOG。已阅读规范、README、进度/决策/问题和app、V1/V2代码。V1原始入口读取路径、输出原尺寸RGBA和实验400×200图；正式适配仅保留原尺寸算法。正式运行无experiments/.local-tests导入（诊断日志仍沿用忽略目录），experiments未改。
已验证：虚拟环境安装opencv-python5.0.0.93、numpy2.5.4、pillow13.0.0；compileall通过；5项unittest通过：中文路径导出与原文件不变、淡灰GIF拒绝且不覆盖既有文件/PNG仍成功、坏图与空白清空结果、正式V1与实验原尺寸逐像素一致、桥接重复请求被拒绝。依赖检查此前成功，本轮扩展检查图像依赖。测试全部合成输入、临时目录，不上传真实材料。
已知：一张几何折线逐像素一致不能代替所有真实图片回归；无新增算法质量声明。用户提供的旧原型人工通过作为历史验收记录；本轮未启动新窗口，拖放、对话框、JS运行、异步响应、真实图视觉与业务GIF可读性均未验证。PNG/GIF格式通过与视觉通过严格区分。
Git初始master，未跟踪.idea为既有用户文件，本轮未触碰；无自动提交或推送。未开发红蓝章、分类、批量或EXE。

## 先前记录
## 本轮提交前复核
用户明确授权提交及推送。已核对master、origin地址、改动文件和依赖清单；git diff --check通过。仅暂存app源码与requirements及相关Markdown，排除.local-tests、.venv和缓存。未重复运行窗口性能测试，未把人工待验项改成通过。Git操作仅使用命令级safe.directory，不更改全局设置。

# 本轮检查：PyWebView原型
环境：Windows11 build26200、Python3.13.17；初始无pywebview/pythonnet，新建项目.venv并安装pywebview6.2.1/pythonnet3.2.1，依赖详见app/requirements.txt。最初受沙箱代理限制的pip查询失败，获得网络执行后安装成功。
已验证：app/main.py --check成功；注册表WebView2 Runtime157.0.4341.46，pythonnet加载及.NET release检查成功；compileall通过；20线程写入JSONL并重新解析20条通过；桥接非法事件拒绝；HTML三资源内联替换和解析检查通过，无外部CDN。查阅官方文档及安装版winforms后端选择、窗口事件和资源加载源码。
未验证：未启动窗口，不执行用户指定人工启动/恢复测试。JS语法/DOM实际执行、桥接、显示、原生标题栏行为、系统首帧、黑屏与GPU冻结均待人工确认；无窗口检查数据不作为启动性能结论。测试步骤及所有指标边界见README。
Git：本轮.git已存在；默认读取报ownership问题；仅命令级safe.directory读取确认master、origin=https://github.com/2081619165/Signing.git。起始工作区干净，未修改任何全局Git配置。新增app及本轮文档是待提交改动；无自动提交推送。
本轮仅新增app原型及维护文档；V1/V2代码未修改。静态页面没有图片输入或算法调用，无业务HTTP服务、Web框架或额外图像依赖。PyWebView传递安装Bottle，但本原型不启动服务器。最终视觉/性能一律待用户验收。

## 上轮检查历史
# 本轮检查报告
2026-11-13 范围：只审查和维护文档，不运行图像算法、不更改Python源码、不开发GUI/EXE。

已检查：AGENTS、README、docs全部6份文档；Signing全部实验脚本、MIT文本、忽略规则、现存V2结果JSON；上游main、seal_extractor、config_loader、配置及依赖/许可。V1/V2均已记录，旧版同一长段重复五份且入口过期，本轮按文档职责整理。第一阶段REVIEW保留，标为历史。

功能：黑签V1/V2已串入实验脚本；PNG、预览、42pxGIF可运行原型。红章只在run.py调用下载快照，不是正式模块；外部上游有批处理、配置、中文路径、等比裁剪等能力，Signing正式业务层尚缺；蓝章上游和Signing均不支持。自动分类与完整业务尺寸选择未实现。

当前证据：gray-v2/results.json六组；faint GIF失败，gray/shadow/white/local_1 GIF记录ok，blank跳过。local_1当前锐化跳过，旧文档回退是历史记录，不将其混用。本轮未重跑历史15项测试或验图；视觉仍未验证。

Git：D:/code/Signing的status、branch、remote均报not a git repository；无本地分支、remote、可查询的已跟踪/未提交清单。磁盘文件存在不等于Git已跟踪。GitHub连接器元数据：public、size0、default_branch main；网页/API浏览失败后改连接器获取。远程tree/main经GitHub连接器返回404并明确说明This repository is empty，确认远程为空，本地文档尚未上传。建议用户ls-remote核验后初始化master，不强推。

未修复代码风险详见BUGS：旧生成器覆盖文档、下载父目录/退出状态、导入副作用、外部硬编码、旧输出残留、成功状态掩盖GIF失败、依赖清单缺失。已有.gitignore仅覆盖.local-tests、.venv、__pycache__、pyc，不能保证任意目录的图片都忽略，提交时必须精确暂存并查看文件清单。

本轮仅更新AGENTS、README、PROGRESS、BUGS、DECISIONS、CHECK_REPORT、CHANGELOG，并给REVIEW添加历史范围说明。没有修改算法、忽略规则或依赖，没有提交/推送。通过静态审查不代表算法视觉验收或GUI就绪。
