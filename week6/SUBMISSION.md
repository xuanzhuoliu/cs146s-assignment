# Assignment 6 提交说明

正式截止日期：**2026 年 11 月 29 日 23:59（Pacific）**，以 [Ed 教师公告](https://edstem.org/us/courses/106077/discussion/8535869) 为准。

## 当前交付

- `run.sh`：通过课程 gateway 运行 Claude Code，先修复和生成报告，再继续同一会话做验收。
- `workflow.md`：通用事故排查流程；没有写死当前事故的答案。
- `writeup.md`：真实实验结果、失败分析、最终配置与尚未取得的正式评分状态。
- `evidence/`：计量日志、评分汇总及实验配置。
- `app/`、`incident/`、`task.md`、`tools/`：官方原始材料，未修改。

## 本地复现

安装并登录 Claude Code，准备 Node 24+、Python 3 和 Go。在本目录运行：

```sh
python3 tools/practice.py --keep
```

由 practice 启动 gateway，再调用 run.sh。不要直接在真实提交目录运行 run.sh，它会修改 app 内的运行时说明，且所有模型调用必须经过 gateway。

练习产生的修复和影响报告只保留在本地 `runs/` 临时实验记录中，不包含在提交包里。正式评分会换入新的事故和代码，由 agent 重新完成任务。

## Gradescope 当前状态与下一步

Autograder 入口已恢复，但 11 月 23 日上传被拒绝，错误是 assignment outline 尚未配置。没有生成正式提交或评分。需等待课程端修复。

1. 课程端修复后，将 `CS146S-week6-submission.zip` 上传到 **Assignment 6 (Autograder)**。压缩包根目录直接包含 `run.sh`，不套一层 week6。
2. 等待评分，保存实际修复分、影响报告分、成本和是否通过。总共最多三次正式提交；当前本次工作尚未使用任何一次。
3. 将实际评分写入 `writeup.md` 的 Part III，更新 GitHub。
4. 向 **Assignment 6 (Writeup)** 提交仓库链接：https://github.com/xuanzhuoliu/cs146s-assignment ，并填写实际用于评分的 commit hash。后续更新报告时必须同时更新此 hash。

目前正式评分栏保留“Not measured”，不能用练习评分冒充。isaackann 和 vdaita 已是仓库 collaborator；mihail911 的邀请已存在，尚待接受。Writeup 表单还要求 patrickhua，目前尚未添加。

## 你需要能解释的三个要点

- **权威来源**：task 和 contracts 定义目标；历史 README、agent 指令和旧测试可能过时。
- **完整修复**：新请求不再出错，并不代表已经排队的旧数据得到处理；升级和重启也要验证。
- **成本与验证**：便宜模型若超时或漏交报告仍然失败；一次通过也不足以判断配置稳定。
