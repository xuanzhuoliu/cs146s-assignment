# Week 5 Readiness Report 运行手册

> 状态：**已完成。** 三份 readiness report 均已生成并保存（2026-11-08 America/Chicago，即 2026-11-09 UTC）。分数与分析见 [`../writeup.md`](../writeup.md)；本文件保留为运行流程记录，不重复分数。

## 完成记录

| 仓库 | 等级 | 通过/评估（跳过） | Report ID | 存储时间 (UTC) |
|---|---|---|---|---|
| dayjs | Level 2 | 20/59 (25) | `6309d0e4-f28b-4f1b-867d-c918f13f45a4` | 2026-11-09 01:34:49 |
| yt-dlp | Level 3 | 29/62 (22) | `85a98749-5843-4b3f-9403-cb374fd2978d` | 2026-11-09 01:35:27 |
| redis | Level 3 | 32/64 (20) | `454d62e7-5c6f-479b-a3eb-5dbc770a13b9` | 2026-11-09 01:36:20 |

- Droid CLI 1.2.0（启动时独立记录），模型 GPT-6.1 Sol (High)；会话 ID 见 `evidence/run-metadata.json`。
- 三个仓库工作区运行前后均未改动（报告 JSON `hasLocalChanges: false`）。
- 实际证据文件名与第 3 节示例不同：`evidence/raw/<repo>-readiness-20261108.typescript`、`<repo>-cli-messages.txt`、`<repo>-report-input.json`、`<repo>-tool-transcript.json`；官方网页导出目前仅有 `dayjs-factory-export.md`（未修改），另两份仍在收集。
- 审计环境未安装 Node/npm、pytest、gh/glab、devcontainer CLI，Redis 未构建；未安装任何依赖。其对评分的影响见 writeup Part II。
- 下方第 0–6 节为准备阶段原文，保留作为过程证据。

## 0. 前置条件：Factory 有效套餐（已解决）

- `/readiness-report` 在 Factory Droid 内运行，需要已登录的 Factory 账号。首次运行曾返回 `No active subscription found`（记录见 `evidence/account-status-20261108.txt`、`evidence/dayjs-attempt-summary.txt`、`evidence/raw/dayjs-readiness.typescript`）；该问题已解决，随后三次正式运行均成功。
- 用户已授权协助注册；设置密码须由本人完成，接受服务条款前须当场确认。先领取课程免费额度，不自行购买订阅。
- 不要用 Factory 官网或博客中的公开示例分数代替实验结果。（准备阶段规则：没跑出来的字段保留占位符；现已全部由实际报告填写。）

## 1. 路径约定

假设当前目录为 `CS146S作业/`（即 `modern-software-dev-assignments/` 的上一级）：

```sh
DROID="$PWD/.tools/factory-1.2.0/droid"      # 已从官方源下载并核验 SHA-256
HW="$PWD/modern-software-dev-assignments/week5"
export FACTORY_DROID_AUTO_UPDATE_ENABLED=false  # 固定已验证的工具版本
mkdir -p "$HW/evidence/raw"
```

三个仓库根目录：`study-repos/dayjs`、`study-repos/yt-dlp`、`study-repos/redis`（均为浅克隆，保持不修改）。

## 2. 运行前：记录元数据 + 确认快照干净

对每个仓库（以 dayjs 为例）：

```sh
cd "$HW/../../study-repos/dayjs"
git rev-parse HEAD                 # 记录 commit SHA
git status --porcelain             # 应为空；若不为空，先停下排查，不要继续
date -u +%Y-%m-%dT%H:%M:%SZ        # 记录 UTC 时间
"$DROID" --version                 # 若该参数不受支持，则以会话界面显示的版本为准
```

预期 SHA（来自本地 `.git/refs/heads/*`，运行时以实际输出为准）：

| 仓库 | 分支 | SHA |
|---|---|---|
| dayjs | dev | `436bde0bcded312781cbe45dc2b0ef079a36d8e3` |
| yt-dlp | master | `b3b18f8fc606e782ee7c82b0780a40c67b829072` |
| redis | unstable | `8e2ba8c4ef6ccf76d327c689cddd5fbe64daa5e5` |

## 3. 运行 `/readiness-report`（每个仓库一次，在仓库根目录）

`/readiness-report` 是 Droid **交互式会话**里的斜杠命令。除非你亲自验证过 Droid 1.2.0 支持非交互方式执行该命令，否则按交互方式操作，不要假设 `droid exec "/readiness-report"` 之类的写法可用。

用 macOS 自带的 `script` 录制整个终端会话：

```sh
cd "$HW/../../study-repos/dayjs"
script -q "$HW/evidence/raw/dayjs-readiness.typescript" "$DROID"
# 进入 Droid 后：
#   1) 如提示登录，由本人完成登录
#   2) 输入：/readiness-report
#   3) 等待报告完整输出；记下界面显示的模型名称、报告 ID / 链接（如有）
#   4) 如果 Droid 提议“自动修复 / 创建 PR / 修改文件”，一律拒绝
#   5) 退出 Droid（Ctrl-D 或 /exit 等）；script 随之结束
```

其余两个仓库同样操作，文件名分别为 `yt-dlp-readiness.typescript`、`redis-readiness.typescript`。

注意：
- `.typescript` 文件含 ANSI 控制字符，是**原始证据**，保存后不要编辑。如需可读版本，另存一份去除控制字符的副本（例如 `col -b < x.typescript > x.txt`），并在 writeup 中注明来源。
- 如果 Factory 网页端 / 控制台另有报告页面，记录其 URL 或 ID；可以导出就导出原文，不要手工重写成“看起来像报告”的文件。
- yt-dlp 的 `.NO_AI/README.md` 禁止用 AI 为该项目**做贡献**。本地只读扫描不属于贡献，但本实验保留该课程推荐仓库用于只读评估，不向其提交任何 AI 生成内容。

## 4. 运行后：确认快照未被改动

```sh
git status --porcelain     # 应仍为空
git rev-parse HEAD         # 应与运行前一致
```

如有改动（例如 Droid 写入了文件），在 writeup 的局限性中如实记录，并用 `git stash`/手动删除前**先看清改动内容**。不要 commit、push。

## 5. 回填 `week5/writeup.md`（全部评分项）

对每个仓库，从报告原文中抄录（不要推测）：

1. **Run metadata 表**：SHA、CLI 版本、模型、UTC 时间、报告 ID/URL。
2. **Summary**：maturity level；阻塞下一等级的 criteria；八个 pillar 的分数。
3. **Failed criteria by pillar**：按八个 pillar 分组列出失败项；报告标为 skipped/unknown 的（尤其是需要 GitHub 管理权限的项）单独注明。
4. **Top remediation suggestions**：报告自己的前几条建议，原文照录。
5. **Raw output**：粘贴三份原始输出（或可读副本）。
6. **Part II**：只在以上数据齐全后再写，逐条检验 H1–H2，并说明 n=3、浅克隆、项目类型偏差等局限。
7. 全文搜索 `PENDING FACTORY RUN`，确认无残留。

## 6. 范围外（本手册不涉及）

不安装各仓库依赖、不运行其测试或脚本、不 push、不添加 collaborators、不提交 Gradescope；这些由本人另行决定。
