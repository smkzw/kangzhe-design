# 安装与迁移

1. 在仓库根目录运行 `python tools/build_dist.py`，得到 `dist/kangzhe-design/`（不含 review、agent、tests、历史样本）。
2. 备份旧的 `kangzhe-design` 与 `kangzhe-design-3d`，移出技能发现目录或用宿主的正式禁用机制停用；不要把新包覆盖解压到仍有旧文件的目录。
3. 把 `dist/kangzhe-design/` 作为一个新目录安装，确认宿主只发现一个 `name: kangzhe-design`。
4. 保留两个指定引擎各自的安装目录：ppt-master 与 html-ppt-skill；不重命名、不替换其 SKILL，不把本包 runtime 当引擎。
5. 首次运行核对 `VERSION` 为 7.0.0、官方 Logo 哈希与 `tokens.logo.sha256` 一致；用 `tools/context_pack.py` 确认读取路径。清理宿主仍引用旧技能内容的任务缓存后，开新任务验证路由。
6. 已有业务产物不会自动迁移。选一个代表性产物，照 `examples/reference/` 的对应轨道重做主题、生图、构图与动效，逐页验收后再批量替换；不覆盖唯一原件，不删用户数据。

6.x 的 page-plan 需把 `contract_revision` 改为 `7.0`，并把 `target_viewports` 换成 `tokens.viewports` 中本轨的浏览器可视区矩阵。本包不修改模型服务配置，不内置账号或密钥，不捆绑字体。
