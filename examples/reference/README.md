# 参考实现

按当前规范做好的正例，照着做即可。内容全部是合成数据（研究资料完整性核对、KZ-118 等虚构研究），不对应真实研究。

| 轨道 | 入口 | 内容 |
|---|---|---|
| 站点式 HTML | `site/index.html`、`site/chapter.html`、`site/clinical.html` | 首页宽屏 Bento 首屏与密排网格；章节页为紧凑章节头 + 密排网格（13 FOLD-06）；临床页放历时变化与累计暴露，模板片段按卡宽缩放 |
| 流式 HTML | `stream/index.html`、`stream/clinical.html` | 章节目录 + 正文阅读栏，目录随阅读位置高亮；临床页同上 |
| HTML-PPT 常规 | `htmlppt/index.html` | html-ppt-skill `new-deck.sh` 原始输出 `scaffold.html` 经 `build.py` 派生，上游 `base.css` / `runtime.js` 原样随包；12 页，电影页与演示页按 scene 步进 |
| HTML-PPT 旗舰 | `htmlppt-flagship/index.html` | 旗舰 F1，见该目录 README |
| PPTX 常规 | `pptx-default/` | ppt-master Default 全流程，见该目录 README |
| PPTX 导出探针 | `pptx/` | 康哲 SVG 写法经 ppt-master 导出后的原生 OOXML，见该目录 README |
| PPTX 旗舰 | `pptx-flagship/`、`pptx-flagship-clinical/` | 旗舰 F1 八页框架；旗舰「层叠纸板」临床模板九页 |
| 演示动画图库 | `../motion/index.html` | 28 种演示形式；`../motion/deck/index.html` 是 HTML-PPT 演示模板组，`../motion/flagship/index.html` 是旗舰 three.js 舞台组件库 |
| 正文模板样张 | `../templates/deck/index.html` | 全部正文模板的 HTML 样张；`../templates/pptx/build.py` 生成同一套 PPTX；`../templates/*.json` 是各模板的示例数据，即数据合同 |

## 共同做法

- 阅读内容写在 HTML 里，脚本只负责行为；没有 JS 时内容仍完整。
- 电影用 `KZMotion.storyboard(states)` 生成关键帧：站点按字数计算停留，最后回到首状态；HTML-PPT 用 `sceneAt` 按 scene 步进。载体内的事实、节点连线与状态条由同一个进度驱动。
- 首屏在 `tokens.viewports` 的每一档视口内一屏放下。
- 正文模板由 `tools/kz_layout.py render` 生成，PPTX 与 HTML 用同一份数据；临床数据先过 `KZClinical` / `tools/kz_layouts` 的合同。

## 图像

`assets/` 的五张 WebP 转码自历史真实生成图，来源哈希见 `assets/provenance.json`。封面类主视觉长边 1672 px，低于 `tokens.image.hero_min_long_edge_px`（2560），正式交付应按 04 生成足够清晰的主视觉与超宽正文背景。
