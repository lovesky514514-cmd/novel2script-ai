# Novel2Script AI

> 七牛云 × XEngineer 暑期实训营第三批次议题三：AI 小说转剧本工具

Novel2Script AI 是一个面向小说作者的 AI 辅助剧本改编工具。项目目标是将 3 个章节以上的小说文本自动转换为结构化剧本 YAML，让作者能够快速获得可编辑、可继续打磨的剧本初稿。

本项目不是简单地把小说一次性丢给大模型生成剧本，而是设计为一个多阶段 AI 改编工作流：

```text
小说文本输入
↓
章节切分
↓
人物 / 事件 / 场景 / 伏笔提取
↓
小说事实记忆库 story_bible / chapter_facts
↓
剧本生成 Agent 改编
↓
剧本医生 / Final Guard 二次校验
↓
YAML Schema 校验
↓
错误知识库 error_patterns 修复
↓
结构化剧本预览与导出
```

## 对应议题

题目三：AI 小说转剧本工具。

要求：

- 能将 3 个章节以上的小说文本自动转换为结构化剧本；
- 输出格式为 YAML；
- 需要提供 YAML Schema 文档；
- Schema 文档需说明字段设计原因；
- 作品需具备完整 README、Demo 视频和可访问代码仓库。

## 项目定位

很多小说作者在改编剧本时会遇到这些问题：

1. 长文本改编时容易遗忘前文人物、伏笔和事件；
2. AI 直接生成剧本时容易胡编、漏情节、人物性格漂移；
3. 普通文本输出不便于后续编辑、拆分和二次创作；
4. 剧本格式不统一，难以被工具继续处理。

Novel2Script AI 重点解决：

- 长上下文下的信息丢失问题；
- 小说到剧本的结构化转换问题；
- AI 输出的格式稳定性问题；
- 剧本初稿的可读性和可编辑性问题。

## 当前实现功能

### 1. 多章节小说输入

支持用户上传小说文本文件，并在首页补充改编要求，例如：

- 重点扩写某一章；
- 保留某个伏笔；
- 对白更自然；
- 压缩支线；
- 强化冲突。

系统会自动读取文本、估算字数，并进入后续生成流程。

### 2. 小说事实抽取

系统会从小说中抽取并保存：

- 角色；
- 人物关系；
- 关键事件；
- 场景地点；
- 时间线；
- 情绪变化；
- 冲突；
- 伏笔；
- 关键道具。

这些信息会组成 `story_bible` 和 `chapter_facts`，供后续剧本生成、校验和修复使用。

### 3. 剧本生成 Agent

剧本生成流程根据小说事实记忆和剧作规则，将小说内容改编为结构化分场剧本。

重点处理：

- 把叙述改成可表演的动作；
- 把心理描写转成对白、神态和行为；
- 保留主要事件与人物动机；
- 增强场景冲突和节奏；
- 将同一章节中的多地点内容拆成更适合拍摄的场景。

### 4. 剧本医生与 Final Guard

系统会对初稿进行二次检查与优化。

检查内容包括：

- 人物是否前后一致；
- 对白是否自然；
- 冲突是否明确；
- 场景是否可表演；
- 是否出现原文不存在的重要人物；
- 是否遗漏关键事件；
- 地点、时间、道具是否来自当前章节事实；
- 是否出现道具串场或地点误判。

### 5. YAML Schema 校验

系统会使用预定义 YAML Schema 和结构校验逻辑检查输出是否完整。

当前输出包含：

- 人物记忆；
- 分场剧本；
- 章节事实；
- 模型调用追踪；
- 修复问题记录；
- 校验报告；
- 质量报告。

### 6. 前端工作台

当前前端已实现：

- 小说文件上传；
- 补充要求输入；
- 生成中进度页；
- 阶段提示；
- 分场剧本预览；
- YAML / TXT 导出；
- 右侧继续修改；
- 功能介绍页；
- 一键启动前后端。

## 技术路线

### 前端

- React
- Vite
- CSS 动效
- 文件上传
- 生成进度页
- 分场剧本预览
- YAML / TXT 下载
- 继续修改输入框

### 后端

- FastAPI
- Pydantic
- PyYAML
- DeepSeek API
- 异步任务管理
- chapter_facts 事实绑定
- YAML 结构化输出
- validation_report / quality_report
- error_patterns.yaml 错误知识库

## 本地运行

### 1. 配置 API Key

复制或新建：

```text
backend/.env
```

填写：

```text
AI_PROVIDER=deepseek
AI_API_KEY=你的 DeepSeek Key
AI_BASE_URL=https://api.deepseek.com/v1
AI_CHAT_MODEL=deepseek-chat
AI_PRO_MODEL=deepseek-reasoner
```

公开仓库中不要提交真实 API Key。

### 2. 一键启动

在项目根目录双击：

```text
start_one_click.bat
```

启动后会自动启动：

```text
FastAPI 后端：http://127.0.0.1:8000
React 前端：http://127.0.0.1:5173
```

## 目录结构

```text
backend/
  app/
    api/
    core/
    knowledge/
    models/
    services/
  tests/

frontend/
  public/
  src/

docs/
  dev_log.md
  logging_privacy.md
  reuse_statement.md
  submission_checklist.md
  yaml_schema.md

run_app.py
start_one_click.bat
README.md
```

## 日志与隐私说明

项目提供本地运行追踪能力，用于排查模型调用、章节事实抽取、生成校验和错误修复过程。

公开仓库不包含：

- 真实 API Key；
- 用户上传的小说原文；
- 真实运行日志；
- 真实模型响应全文；
- `debug_runs` 调试目录。

系统保留的追踪字段包括：

- `model_trace`；
- `chapter_facts`；
- `repair_questions`；
- `validation_report`；
- `quality_report`；
- `error_patterns.yaml`。

这些字段用于解释生成过程和改进错误知识库，不用于公开保存用户隐私文本。

## 原创与复用说明

本项目围绕题目三重新实现。项目参考本人历史项目中的产品设计经验和工程组织思路，但不直接复制历史项目作为主体工程。

详细说明见：

```text
docs/reuse_statement.md
```

## YAML Schema 文档

详细字段说明见：

```text
docs/yaml_schema.md
```

## 当前分支

Day 2 任务建议提交到：

```text
feature/day2-fullstack-polish
```
