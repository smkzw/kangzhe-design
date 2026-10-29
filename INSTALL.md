# 安装与迁移

## 安装（任意支持 SKILL.md 技能目录的 agent）

1. 从 GitHub Release 下载 `kangzhe-design-<版本>.zip`，解压后得到 `kangzhe-design/` 目录（其中有 `SKILL.md`）。从仓库安装时，先在仓库根目录运行 `python3 tools/build_dist.py`，用生成的 `dist/kangzhe-design/`。
2. 把整个目录放进宿主的技能目录，目录名保持 `kangzhe-design`：

   | 宿主 | 位置 |
   |---|---|
   | Claude Code | `~/.claude/skills/kangzhe-design/`（项目级：`<项目>/.claude/skills/kangzhe-design/`） |
   | Codex | `~/.codex/skills/kangzhe-design/` |
   | 其他读 `SKILL.md` 目录的宿主 | 该宿主的技能目录，例如 `~/.agents/skills/kangzhe-design/` |

3. 安装工具依赖（Python 3.10+）：`python3 -m pip install -r kangzhe-design/requirements.txt`。
4. 另外安装两个制作引擎，各自独立成技能，不改名、不改它们的 SKILL：
   - PPTX：[hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) 的 `skills/ppt-master/`，并安装它自己的 `requirements.txt`。本版核对 `523e5bd`（v6.7.3 之后两个修复提交）。
   - HTML-PPT：[lewislulu/html-ppt-skill](https://github.com/lewislulu/html-ppt-skill)（技能名 `html-ppt`）。本版核对 `fd16290`。
   站点式与流式 HTML 只需要本技能。
5. 自检：`python3 kangzhe-design/tools/context_pack.py --track pptx --stage bootstrap` 能列出文件；`VERSION` 与 `STATUS.md` 版本一致；`assets/logo_bot.svg`、`assets/logo_bot.png` 的 SHA-256 等于 `tokens/tokens.json` 的 `logo.sha256`、`logo.png_sha256`；缺省背景套 `assets/backgrounds/` 的哈希等于 `default-set.json`（`python3 kangzhe-design/tools/qc_plan.py kangzhe-design/examples/reference/pptx-default/page-plan.json` 不报哈希错）；`python3 kangzhe-design/tools/check_edge_bars.py kangzhe-design/examples/reference/pptx-default/svg` 退出码 0。开一个新会话，确认宿主只发现一个 `name: kangzhe-design`。

本包不修改模型服务配置，不内置账号或密钥，不捆绑字体（PPTX 用目标机已有的 Microsoft YaHei 与 Arial）。安装包不含维护资料（`review/`、`agent/`、`tests/`、历史样本）与 `.pptx` 样例成品；样例成品作为 Release 附件提供。

## 从 6.x 迁移

1. 备份旧的 `kangzhe-design` 与 `kangzhe-design-3d`，移出技能目录或用宿主的禁用机制停用；不要把新包覆盖解压到仍有旧文件的目录。
2. 清理宿主仍引用旧技能内容的任务缓存后，开新任务验证路由。
3. 已有业务产物不会自动迁移。选一个代表性产物，照 `examples/reference/` 的对应轨道重做主题、生图、构图与动效，逐页验收后再批量替换；不覆盖唯一原件，不删用户数据。
4. 6.x 的 page-plan 需把 `contract_revision` 改为 `7.0`，并把 `target_viewports` 换成 `tokens.viewports` 中本轨的浏览器可视区矩阵（PPTX 为 `[[1280,720]]`）。
