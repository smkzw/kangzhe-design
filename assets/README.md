# assets：品牌与素材

| 目录 / 文件 | 内容 | 用法 |
|---|---|---|
| `logo_bot.svg`、`logo_bot.png` | 官方康哲标识，逐字节保留原件 | 哈希登记在 `tokens/tokens.json` 的 `logo.sha256`、`logo.png_sha256`；不改色、不改字、不加折射、不重绘（01 CORE-02） |
| `header-mark/` | PPTX 与 HTML-PPT 正文页的双菱形：`source-native.xml` 是参考 PPTX 中的四个原生品牌形状，`header-mark.svg` 由 `tools/brand_fragments.py` 派生供 HTML 使用，来源见 `provenance.json` | 只用于这两轨的正文页，站点与流式不用（02 LG-03） |
| `backgrounds/` | 常规路线缺省背景套：A2（缺省，暖纸底 + 生成的液态玻璃丝带）、A1、B、C 四种风格 × 封面 / 目录 / 章节 / 尾页 / 正文 × 16:9 与 21:9；`flagship/` 是旗舰封面与暖白画布 | 没有生图能力或用户选用现成风格时使用（04 IMG-07）；page-plan 写 `default_set` / `flagship_set` 与清单里的 id，哈希由 `tools/qc_plan.py` 核对 |
| `icons/` | 线性图标（24×24，stroke 1.8）；`source: kangzhe` 为本包绘制，`source: tabler` 取自 Tabler Icons，许可见 `NOTICE.md` | 经 `runtime/kz-icons.js` 或 `tools/kz_layouts/icon_pick.py` 取用，按内容选图标 |
| `metric/` | 智研 METRIC 平台与子系统（T/R/E/M/C/I/P/L）标识，`-header` 版去掉四周留白供网页页头使用，来源见 `provenance.json` | 页头规范见 `design_specs/16-metric-subsystem-header.md`；子系统页头不放康哲标志 |
| `vendor/` | Apache ECharts 6.1.0、GSAP 3.15.1（含 DrawSVG、MotionPath、CustomEase、Flip、MorphSVG）、three.js 旗舰舞台包（three.js、postprocessing、N8AO），各自的 LICENSE / NOTICE 同目录 | 本地加载，不从 CDN 取用 |

品牌素材仅供有权使用康哲与 METRIC 品牌的用户使用。本包不含字体、原始临床资料或真实业务数据。
