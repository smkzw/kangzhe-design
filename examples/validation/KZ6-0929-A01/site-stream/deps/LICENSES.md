# 依赖来源与许可

本目录的运行时依赖从唯一新版技能包原样复制，**未修改**。原包与上游只读。

来源：`kangzhe-design/（已安装的 6.0.0 技能根目录）`（`kangzhe-design 6.0.0`，`VERSION` sha256 `54ef76332b31df830699e9d4138396885ab72bae260a034a81ff02bf32d8e90a`）

| 本目录文件 | 取自（相对技能包根，非本目录内路径） | sha256 | 许可 |
|---|---|---|---|
| `kz-tokens.css` | `kangzhe-design/runtime/kz-tokens.css` | `1e33eabb5699e7d169031ba403b46d0bbfef4fad401be9722fbf2391519aacda` | 随主包（康哲内部设计系统资产） |
| `kz-tokens.js` | `kangzhe-design/runtime/kz-tokens.js` | `4ed20635089707761ac9e9be092b86a1041ee4a8dacc0f0ec26a557601105184` | 同上 |
| `kz-glass.css` | `kangzhe-design/runtime/kz-glass.css` | `5a3b127220307e16252bac4ed952322c73ee11d00b9a6f2c5a1872370b6c85e8` | 同上 |
| `kz-motion.js` | `kangzhe-design/runtime/kz-motion.js` | `759c515d1712b99a90a2851696184fe470588986e61e846ccae65c0ffcfb8355` | 同上 |
| `kz-drilldown.js` | `kangzhe-design/runtime/kz-drilldown.js` | `ffa0abb071dc23a7280037b46bf2b57aa47dbd405af4bbb6d492ba64b96897be` | 同上 |
| `kz-charts.js` | `kangzhe-design/runtime/kz-charts.js` | `aa8d22a1bebf66de7c755bd2f713843e9eef9e0932ae8e1e9da9c01075ccacf1` | 同上 |
| `logo_bot.svg` | `kangzhe-design/assets/logo_bot.svg` | `8d16d3ae8353dd31f46a50d401e66f9e62af40be6cc42cdf5050866a4e6e1cae` | 康哲药业官方标识。字形、色彩、比例、字距未改；未做玻璃化、拉伸或发光。哈希与 `tokens/tokens.json#logo.sha256` 一致 |
| `vendor/echarts.min.js` | `kangzhe-design/assets/vendor/echarts.min.js` | `b66b25aeb4df84e33199dc21694014d336d222cbd9deb0e5a7c14bd6aa0d0fd0` | Apache License 2.0 |
| `vendor/ECHARTS-LICENSE.txt` | `kangzhe-design/assets/vendor/ECHARTS-LICENSE.txt` | — | Apache License 2.0 全文（原样保留） |
| `vendor/ECHARTS-NOTICE.txt` | `kangzhe-design/assets/vendor/ECHARTS-NOTICE.txt` | — | NOTICE 文件（原样保留） |

本 pass 自撰文件（非上游）：`kz-data.js`、`kz-films.js`、`kz-site.css`、`kz-app.js`、`LICENSES.md`。
字体不随包分发（`tokens.fonts.redistribute = false`），HTML 只声明字体族回退链。

`file://` 与 HTTP 两种方式均可运行：全部依赖为相对路径的本地文件，无远程请求、无 fetch、无模块打包。
