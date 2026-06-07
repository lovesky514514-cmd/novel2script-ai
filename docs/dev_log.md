# Development Log

## Day 1：项目初始化

已完成：

- 初始化 GitHub 仓库；
- 建立基础目录结构；
- 创建项目说明文档；
- 创建 YAML Schema 初版；
- 创建复用说明与合规说明；
- 初始化 FastAPI 后端骨架。

## Day 2：前后端完整链路整合

已完成：

- 搭建 React + Vite 前端工作台；
- 搭建 FastAPI 后端接口；
- 接入 DeepSeek API；
- 实现小说上传、补充要求输入和任务生成；
- 实现生成中页面、进度条和阶段提示；
- 修复生成时打开新标签的问题；
- 实现结果页左右布局；
- 左侧展示分场剧本，右侧支持继续修改；
- 支持 YAML / TXT 导出；
- 增加 `story_bible`、`chapter_facts`、`model_trace`、`repair_questions`；
- 增加 `validation_report` 和 `quality_report`；
- 增加 `error_patterns.yaml` 错误知识库；
- 清理 public 图标，只保留 favicon；
- 补充日志、隐私、复用、比赛提交说明；
- 准备 GitHub 分支提交版本。

## PR 记录

| PR | 内容 | 状态 |
|---|---|---|
| PR 1 | 初始化项目说明、Schema 文档与合规说明 | 已完成 |
| PR 2 | 初始化 FastAPI 后端与基础接口 | 已完成 |
| PR 3 | 集成前后端小说转剧本工作流 | 待提交 |

## 当前分支建议

```text
feature/day2-fullstack-polish
```

## 提交信息建议

```text
Day 2: integrate fullstack Novel2Script pipeline
```
