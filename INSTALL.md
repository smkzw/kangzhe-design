# 安装

## 1. 取得发布包

从 GitHub Release 下载 `kangzhe-design-8.0.0.zip` 与 `SHA256SUMS`，核对后解压：

```bash
shasum -a 256 -c SHA256SUMS        # 应显示 kangzhe-design-8.0.0.zip: OK
unzip kangzhe-design-8.0.0.zip     # 得到 kangzhe-design/（其中有 SKILL.md）
```

仓库 main 分支的内容与 zip 解压后的 `kangzhe-design/` 相同，也可以直接克隆仓库使用，不需要构建。

## 2. 放进技能目录

整个目录放进宿主的技能目录，目录名保持 `kangzhe-design`：

| 宿主 | 位置 |
|---|---|
| Claude Code | `~/.claude/skills/kangzhe-design/`（项目级：`<项目>/.claude/skills/kangzhe-design/`） |
| Codex | `~/.codex/skills/kangzhe-design/` |
| 其他读 `SKILL.md` 目录的宿主 | 该宿主的技能目录，例如 `~/.agents/skills/kangzhe-design/` |

升级时先把旧目录移出技能目录（备份），再放入新目录；不要把新包覆盖解压到旧目录上，旧文件会残留。

## 3. 依赖

- Python 3.10+：`python3 -m pip install -r kangzhe-design/requirements.txt`（`jsonschema`、`Pillow`、`numpy`）。
- 两个制作引擎，各自作为独立技能安装，不改名、不改它们的 SKILL：
  - PPTX：[hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) 的 `skills/ppt-master/`，并安装它自己的 `requirements.txt`。本版核对基线 `523e5bd`（v6.7.3 之后两个修复提交）。
  - HTML-PPT：[lewislulu/html-ppt-skill](https://github.com/lewislulu/html-ppt-skill)（技能名 `html-ppt`）。本版核对基线 `fd16290`。
- 站点式与流式 HTML 只需要本技能。
- PPTX 使用目标机已安装的 Microsoft YaHei 与 Arial；本包不捆绑字体。

## 4. 自检

```bash
KZ=~/.claude/skills/kangzhe-design
python3 $KZ/tools/context_pack.py --track pptx --stage bootstrap      # 能列出要读的文件
python3 $KZ/tools/kz_layout.py list | tail -1                          # 50 templates
python3 $KZ/tools/qc_plan.py $KZ/examples/reference/pptx-default/page-plan.json   # 退出码 0，没有 error 级发现
python3 $KZ/tools/check_edge_bars.py $KZ/examples/reference/pptx-default/svg_output  # 退出码 0
```

另外确认：`VERSION` 为 `8.0.0`，与 `SKILL.md` 标题一致；`assets/logo_bot.svg`、`assets/logo_bot.png` 的 SHA-256 等于 `tokens/tokens.json` 的 `logo.sha256`、`logo.png_sha256`；`PACKAGE_MANIFEST.json` 列出的每个文件哈希一致。开一个新会话，确认宿主只发现一个 `name: kangzhe-design`。

本包不修改模型服务配置，不含账号或密钥。

## 从旧版本迁移

1. 备份并移走旧的 `kangzhe-design`（以及更早的 `kangzhe-design-3d`），清理宿主里引用旧技能内容的任务缓存后开新会话。
2. 已有产物不会自动迁移。选一个代表性产物，照 `examples/reference/` 对应轨道重做背景、构图与动效，逐页验收后再批量替换；不覆盖唯一原件。
3. 6.x 的 page-plan 把 `contract_revision` 改为 `7.0`，`target_viewports` 换成 `tokens.viewports` 中本轨的浏览器可视区矩阵（PPTX 为 `[[1280,720]]`）。7.x 与 8.0 的合同修订号相同（`7.0`），7.x 的 page-plan 先用 `tools/qc_plan.py` 预检，按报错补字段。
