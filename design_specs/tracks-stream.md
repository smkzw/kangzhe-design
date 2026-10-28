# 流式 HTML 轨道

按文档或电子书阅读组织章节，有固定目录与章节锚点，不是一串 16:9 幻灯片，也不使用双菱形。

## 步骤
1. **计划**：事实清单 → 章节树 → page-plan（`track: stream`，`body_profile: responsive`，`target_viewports` 取 `tokens.viewports.stream`）→ 首页与一级章节入口的 film-plan 或 `fold_stage` 理由 → `tools/qc_plan.py`。
2. **资产**：首页首屏用生成主视觉或程序化光场（04 IMG-01）。
3. **页面**：首页 Bento 首屏，正文三栏，章节 `data-kz-section` 入场，明细下钻；接线与站点式相同（参考实现 `examples/reference/stream/index.html` 复用 `site.js` 的 `KZRefSite.mount('home')`）。
4. **验收**：同站点式，另验目录高亮随阅读位置变化、打印保留全文。

## 要点

- 文档首页：13 FOLD-01/02 的 Bento 首屏，电影建立全文结构概览；一级章节入口有章节电影或章节首区块。
- 正文：“目录 · 正文 · 宽栏”三栏（13 FOLD-05），正文栏宽等于行长 `--kz-measure`，同章节的图表、表格或注释在右侧宽栏与正文并排；逐屏密度按 13 FOLD-07 验收；章节首次可见时入场；目录随阅读位置高亮。正文允许自然高度，不把所有段落包成等高卡。
- 下钻：一级卡是摘要，二级容器可有多卡、多图和原文，必要时三级；弹窗宽度与内容密度匹配。
- 电影离屏停帧，阅读下方段落时后台不持续耗资源。
- 侧注、正文卡与下钻面板没有全高或全宽的边缘色条（02 LG-02）；侧注靠位置与小标题区分，不靠左侧色条。
- 引用按 03 COPY-05；标题是内容名称，观点放在导语或结论段。
- 打印保留全文与关键明细，不让折叠后只剩标题。
- 验收视口 `tokens.viewports.stream`；没有人声讲解任务时不写讲稿，G7-NOTES 写 N/A 与原因。

参考实现：`examples/reference/stream/index.html`。
