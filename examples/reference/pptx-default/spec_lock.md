<!-- ppt-master-schema: spec-lock/v1 -->
# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## communication
- primary_language: zh-CN
- audience: 产品中心医学部内部例会的同事，关心资料是否齐全、缺口由谁补、何时能进入比较
- objective: 报告资料完整性核对结果与缺口处理口径，并让与会者认可 2027Q1 内完成补收与版本确认的分工
- core_message: 资料整体可用，但中心记录与安全性报告共缺 4 份、两版方案有 2 项差异；补收与确认在 2027Q1 内完成后再做组间比较
- consumption_mode: balanced

## mode
- mode: custom
- mode_behavior: 封面即给出核对结论；目录按范围、结果、计划三步；正文页标题写内容名称，页内先放关键事实再放解释；资料完整性页用原生分组柱图配一句观点句，核对计划页用原生形状甘特；结束页落到会上需要确认的两件事。

## visual_style
- visual_style: custom
- visual_style_behavior: 康哲 Liquid Glass：近白浅底；正文页固定 chrome（左上原生双菱形、单行页标题、橙色横线、右上官方 Logo、两槽页脚）；内容放在同族玻璃卡里，三停近白半透明渐变面、中性细折光边与顶边短高光、一个暖褐柔和外阴影三者叠加；卡标题加粗墨色，正文分条，重点加粗、关键缺口深红；不用通长彩色边条；数据面平直不透视。

## colors
- background: #FBFCFD
- secondary_bg: #FFFFFF
- primary: #FF9900
- accent: #FFCC00
- secondary_accent: #C00000
- body_text: #404040
- secondary_text: #64676B
- divider: #CED3D8
- ink: #0F1115
- footer: #808080
- chart_comparator: #6E7B8C
- chart_series_1: #D46B08
- chart_grid: #E7EBEE
- dept_medical: #FF9900
- dept_statistics: #587B3B
- dept_pv: #A85F34

## typography
- font_family: Microsoft YaHei, Arial, sans-serif
- title_family: Microsoft YaHei, Arial, sans-serif
- body_family: Microsoft YaHei, Arial, sans-serif
- body: 20
- title: 32
- subtitle: 24
- annotation: 16
- card_title: 24
- takeaway: 24
- footer: 18
- cover_title: 56
- hero_subtitle: 28
- hero_meta: 20
- toc_title: 48
- toc_number: 40
- toc_label: 32
- ending_title: 104

## icons
- library: none
- inventory: none

## images
- cover: images/cover_hero.png | source=user | crop=adaptive
- toc: images/toc_hero.png | source=user | crop=adaptive
- body: images/body_quiet.png | source=user | crop=adaptive
- ending: images/ending_hero.png | source=user | crop=adaptive
- logo: images/logo.png | source=user | crop=no-crop

## page_rhythm
- P01: anchor
- P02: anchor
- P03: dense
- P04: dense
- P05: dense
- P06: anchor

## page_visualizations
- P04: chart/grouped_bar_chart
- P05: chart/gantt_chart

## pptx_structure
- mode: flat

## forbidden
- `mask`, `<style>`, `class`, external CSS, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<set>`, `<script>` / event attributes, `<iframe>`
- HTML named entities in text; write typography as raw Unicode and escape XML reserved characters
