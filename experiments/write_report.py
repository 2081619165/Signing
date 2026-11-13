from pathlib import Path
import json,sys,importlib.metadata as md
r=Path('.'); data=json.loads((r/'.local-tests/results.json').read_text(encoding='utf8'))
versions='\n'.join(f'- {p}: {md.version(p)}' for p in ['pillow','numpy','opencv-python','scipy'])
review='''# 源码审查与实验结论（2026-11-13）

## 固定版本
- https://github.com/show7/signature-extractor ：f7da5df17bda46a56bf588baa78843baa5b8779a
- https://github.com/leopens/seal-extractor ：4e571b3f25cc8431756476e96976c392abda398e
通过 GitHub API 固定 SHA 下载相关文本源码，未整体导入 Signing。README、LICENSE、show7 依赖声明、配置加载器、main.py、seal_extractor.py 和 leopens scripts/extract_seal.py 已审查。未执行上游技能指令。

## 算法比较
| 项目 | show7 | leopens |
|---|---|---|
| 背景/阴影 | 大核膨胀估计背景、除法平场、归一化 | 红色优势度 R-(G+B)/2；中性灰背景可排除，暖色纸不保证 |
| 签名 | Otsu 且阈值上限220，纯黑输出 | 不支持 |
| 淡笔保护 | 无专门保护；开运算至少3像素，会删细线，闭运算可能粘连 | 软 alpha 保留淡红，但阈值18及40像素连通域过滤会删弱小笔画 |
| 红章 | HSV 两段，S/V>=40，2x2开闭，默认增强红色 | 红色优势度软阈值18/75，统一重染214,40,32 |
| 透明 | 模糊 mask，带 mask paste 再次乘 alpha，边缘减弱 | 墨量作为 alpha，旋转插值 |
| 裁剪 | 行列投影阈值可能切细线尾部，按比例装入画布 | alpha>8边界加24像素；自动旋转依赖圆章双侧空弧结构 |
| 颜色 | 签名纯黑；红章默认 R+20 G/B-20，颜色改变 | 固定红色，不能作为保真提取 |
| Windows | 中文路径字节解码；本轮函数调用成功 | Pillow路径；本轮函数调用成功 |

两者均 MIT，复用实质源码需保留版权及许可文本。show7 依赖 OpenCV/NumPy/Pillow；leopens 为 Pillow/NumPy/SciPy。依赖发行包还有独立许可证及打包附带许可，正式分发前需逐项核验（本轮未验证完整传递依赖许可证）。不需要 GPU 或在线推理。未验证所有 Python/Windows 组合。

## 样本与参数
自制公开可复现的几何折线、TEST ONLY圆形图案，无真实印签。640×360；1像素下划线专门检查细笔画。white/gray/faint/red/pale_red/blue/shadow 七类。不是自然手写或真实复杂印章，不能外推业务通过率。灰底185；淡笔190/背景245；淡红240,200,200；阴影从0.48到1线性渐变。
调用上游原始函数默认参数，不修改第三方源码。show7 签名400×200、红章300×300；leopens默认自动旋转、lo18/hi75/min_speck40/pad24。蓝章两者标不支持，leopens签名标不支持，不伪造输出。详细逐图记录见 .local-tests/results.json。

## 输出验证与风险
8项支持的运行全部成功，8张PNG均重新读取检查存在透明和非透明像素。透明存在不等于灰底完全去除或视觉合格。所有视觉结果待人工确认，未认定业务质量通过。
20张GIF重新读取，尺寸全部符合预期；17张透明且非空，leopens浅红章3张全透明，判为失败。GIF仅一位透明，本轮采用alpha>=128，淡红半透明墨迹因此消失，不补画。GIF用于格式实验，不能据此认定效果较好。
签名高42和34，宽138和111；章画布60×60、151×106、151×151，内容等比居中留白。圆形测试图放入矩形仅验证画布，不代表建造师真实章样本。96DPI下毫米=像素×25.4/96：60=15.875mm，151=39.952mm，106=28.046mm，42=11.1125mm，34=8.996mm。GIF不可靠保存DPI，按像素与96DPI解释，不宣称已写入物理DPI。

## 建议
可有条件复用局部思路，暂不整体采用。show7适合背景校正基线，但细线保护、alpha重复相乘和纯黑化需评估；leopens适合淡红PNG实验，但重染、自动旋转结构假设和GIF淡墨丢失是明确风险。蓝章另立后续需求，本轮不改造。先人工检查对比图及小尺寸GIF，再决定是否推进；不自动进入下一阶段。
'''
(r/'docs/REVIEW.md').write_text(review,encoding='utf8')
for name,txt in {
'PROGRESS.md':'# 最新进度\n2026-11-13：规范、源码审查、七类合成输入与8项支持运行完成。输出 .local-tests/results；逐图结果 .local-tests/results.json。下一步仅等待用户人工检查，不进入正式软件开发。初始目录非Git仓库，无提交推送。',
'DECISIONS.md':'# 技术决策\n本轮仅独立算法实验。第三方源码及图片放忽略目录；experiments保存复现脚本。不整体移植，不开发GUI/EXE。仅用虚构图案；不采用颜色保真或视觉合格的未经验证声明。等比缩放加透明留白；GIF用128透明阈值且保留失败结果。详见 REVIEW.md。',
'BUGS.md':'# 已知问题\n已验证：leopens浅红输出转GIF后3种尺寸均全透明（失败，未修复）。\n源码确认风险：show7至少3像素开运算会删除单像素线；闭运算可能粘连；带mask粘贴使alpha再次相乘。leopens固定重染，不保原色；小连通域删除可能损伤细笔。两项目蓝章不支持。\n待人工确认：断笔、粘连、过黑、残底、小尺寸可读性及旋转方向。',
'CHANGELOG.md':'# 修改日志\n2026-11-13：建立规范与docs；新增固定源码下载和独立合成实验脚本；生成7类原图、8张透明PNG、白底/棋盘格对比图、20张GIF及JSON；记录3张GIF全透明失败。未修改上游算法，未推送。',
'CHECK_REPORT.md':'# 检查报告\n已验证：Windows Python '+sys.version.split()[0]+'；原始函数8次运行成功；8张PNG含alpha0及非零；20张GIF尺寸正确，17张透明且非空，3张全透明失败。\n未验证：视觉质量、真实材料、复杂光照、自然手写及全部许可证传递依赖；待人工确认。\nGit初始状态：目录为空、非Git仓库，因此不存在git状态/忽略规则实测，未初始化。实验目录由.gitignore声明忽略。Git clone失败后改API固定SHA获取成功。\n环境依赖（安装在现有Python环境，非独立venv）：\n'+versions+'\n复现：python experiments/fetch_sources.py；python experiments/run.py。下载脚本固定版本需使用 REVIEW 中SHA（不得将未来main视为本次版本）。完整参数、逐图状态见 .local-tests/results.json；源码快照见 .local-tests/*/VERSION.json。'
}.items():(r/'docs'/name).write_text(txt+'\n',encoding='utf8')
# 将下载脚本固定到本轮提交。
p=r/'experiments/fetch_sources.py';s=p.read_text(encoding='utf-8');s=s.replace("'/commits/main'","'/commits/'+{'show7/signature-extractor':'f7da5df17bda46a56bf588baa78843baa5b8779a','leopens/seal-extractor':'4e571b3f25cc8431756476e96976c392abda398e'}[repo]");p.write_text(s,encoding='utf8')
print('docs written')
