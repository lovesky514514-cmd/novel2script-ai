# 开发日志

本文件用于记录 Novel2Script AI 在七牛云 × XEngineer 暑期实训营第三批次中的持续开发过程。

## 批次信息

- 比赛：七牛云 × XEngineer 暑期实训营
- 批次：第三批次
- 开发周期：2026-06-05 00:00 至 2026-06-07 23:59
- 选择议题：题目三，AI 小说转剧本工具

## 开发原则

1. 按功能拆分小 PR；
2. 每个 PR 只做一件事；
3. 主分支保持可运行；
4. PR 描述必须包含功能描述、实现思路和测试方式；
5. 若复用本人历史项目代码或思路，必须在 PR 中注明来源；
6. 第三方依赖必须在 README 中列明；
7. 每次提交都需要有明确功能目的，避免无意义 commit。

## 开发记录

### Day 1：项目初始化

#### 已完成

- 创建项目仓库；
- 初始化 README；
- 初始化 YAML Schema 设计文档；
- 初始化复用说明；
- 初始化 PR 模板；
- 明确项目技术路线；
- 明确小说转剧本的多阶段工作流；
- 初始化 FastAPI 后端基础结构。

#### 当前思路

项目不采用“一次性 AI 生成剧本”的方式，而是采用多阶段工作流：

```text
小说输入
↓
章节切分
↓
事实抽取
↓
角色 / 事件 / 伏笔 / 时间线记忆库
↓
剧本生成 Agent
↓
剧本医生 / Final Guard
↓
YAML Schema 校验
↓
自动修复
↓
结果预览与导出
```

---

### Day 2：核心工作流开发

#### 已完成

- 搭建 React + Vite 前端工作台；
- 搭建 FastAPI 后端接口；
- 接入 DeepSeek API；
- 实现小说上传、补充要求输入和异步生成任务；
- 实现生成中页面、进度条和阶段提示；
- 修复生成时浏览器打开新标签的问题；
- 实现结果页左右布局；
- 左侧展示分场剧本，右侧支持继续修改；
- 支持 YAML / TXT 导出；
- 增加 `story_bible`、`chapter_facts`、`model_trace`、`repair_questions`；
- 增加 `validation_report` 和 `quality_report`；
- 增加 `error_patterns.yaml` 错误知识库；
- 增加日志与隐私说明；
- 清理 public 图标，只保留 favicon；
- 准备 `feature/day2-fullstack-polish` 分支提交版本。

#### 当前结果

Day 2 已经完成从“后端初始化”到“前后端可运行原型”的升级。

当前项目可以完成：

```text
小说文本上传
↓
用户补充要求输入
↓
后端异步生成
↓
生成进度展示
↓
分场剧本预览
↓
YAML / TXT 导出
↓
继续修改
```

---

### Day 3：体验优化与 Demo

#### 计划

- 完善 Demo 示例；
- 录制 Demo 视频；
- 补充在线访问地址；
- 完善比赛提交说明；
- 根据评审要求补充截图和运行说明；
- 合并 Day 2 分支到主分支。

## PR 记录

| PR | 内容 | 状态 |
|---|---|---|
| PR 1 | 初始化项目说明、Schema 文档与合规说明 | 已完成 |
| PR 2 | 初始化 FastAPI 后端与基础接口 | 已完成 |
| PR 3 | 集成前后端小说转剧本工作流 | 待提交 |

## Commit 记录说明

本项目使用语义化 commit，示例：

```text
docs: initialize project documents
chore: initialize backend service
feat: integrate fullstack novel2script pipeline
fix: prevent browser from opening file in new tab
docs: align day2 documentation with implemented workflow
```

## 当前分支建议

```text
feature/day2-fullstack-polish
```

## 提交信息建议

```text
Day 2: integrate fullstack Novel2Script pipeline
```
