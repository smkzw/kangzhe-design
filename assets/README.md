# 素材说明

`logo_bot.svg` 是上传旧包中的原始康哲标识，逐字节保留；不作为可生成的概念 Logo，不添加折射、改字、换色。仅供有权使用该标识的用户使用。

`vendor/echarts.min.js` 来自上传旧包，实际运行版本为 6.1.0。保留 Apache 2.0 LICENSE 和 NOTICE。没有重新从不明 CDN 获取。

没有打包字体、GSAP、模型查看器、原始临床资料、用户示例网站的业务数据或整套旧规范。字体使用本机已合法安装的版本。演示使用虚构数据。

`header-mark/source-native.xml` 仅包含用户指定参考 PPTX 的四个品牌形状，无临床内容或整页资料；原生结构逐项保留。`provenance.json` 记录来源文件 hash、页号和形状名称。`header-mark.svg` 由 `tools/brand_fragments.py` 派生，用于 HTML；禁止手动重画或引入其他材质。仅供有权使用该品牌的用户使用。

`backgrounds/` 是缺省背景套（04 IMG-07）：封面、目录、章节、尾页主视觉与一张正文安静背景，取自康哲 A03 批次的历史真实生图，JPEG q90 转码，未重新生成。只在用户确认没有生图能力时使用；清单、哈希与已知限制见 `backgrounds/default-set.json`。
