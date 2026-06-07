# Novel2Script AI

Novel2Script AI 是一个面向小说文本改编的 AI 工具原型，用于将小说章节转换为结构化分场剧本。

本项目不是单纯聊天页面，而是围绕“小说上传 → 章节事实抽取 → 分场剧本生成 → 质量校验 → 错误知识库沉淀 → 结构化导出”的完整工作流实现。

## 当前版本

```text
day2_fullstack_polish
```

## 核心功能

- 小说文本文件上传；
- 用户补充改编要求；
- 章节解析与基础事实抽取；
- `story_bible` / `chapter_facts` 生成；
- 分场剧本预览；
- YAML / TXT 导出；
- 右侧继续修改；
- 生成中进度页与阶段提示；
- `validation_report` / `quality_report` 质量报告；
- `model_trace` 模型链路追踪；
- `repair_questions` 修复问题记录；
- `error_patterns.yaml` 错误知识库；
- 一键启动前后端。

## 技术架构

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

1. 进入项目根目录。
2. 打开 `backend/.env`。
3. 填写 DeepSeek API Key。
4. 双击：

```text
start_one_click.bat
```

启动后会自动启动：

```text
FastAPI 后端：http://127.0.0.1:8000
React 前端：http://127.0.0.1:5173
```

## API Key 配置

在 `backend/.env` 中填写：

```text
AI_PROVIDER=deepseek
AI_API_KEY=你的 DeepSeek Key
AI_BASE_URL=https://api.deepseek.com/v1
AI_CHAT_MODEL=deepseek-chat
AI_PRO_MODEL=deepseek-reasoner
```

公开仓库中不要提交真实 API Key。

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

## 错误知识库

错误知识库文件：

```text
backend/app/knowledge/error_patterns.yaml
```

当前用于沉淀常见生成问题，例如：

- 日期中的“日”被误判为场景时间；
- 短信/录音人物被误判为现场人物；
- 地点词被误判为道具；
- 不同章节道具串场；
- 多地点章节需要拆场；
- 旧修复日志干扰最终判断。

## 日志与隐私说明

本项目提供本地运行追踪能力，用于排查模型调用、章节事实抽取、生成校验和错误修复过程。

公开仓库不包含：

- 真实 API Key；
- 用户上传的小说原文；
- 真实运行日志；
- 真实模型响应全文；
- `debug_runs` 调试目录。

系统保留的追踪字段包括：

- `model_trace`
- `chapter_facts`
- `repair_questions`
- `validation_report`
- `quality_report`
- `error_patterns.yaml`

这些字段用于解释生成过程和改进错误知识库，不用于公开保存用户隐私文本。

## 比赛提交说明

本项目使用 DeepSeek API 作为大模型能力来源，前后端、流程编排、事实绑定、错误知识库、校验报告和导出结构均围绕本项目重新实现。

项目不内置未授权小说、影视剧本或课程内容。演示时建议使用自写样例文本或已授权文本。

## GitHub 分支说明

Day 2 任务建议提交到分支：

```text
feature/day2-fullstack-polish
```

建议提交信息：

```text
Day 2: integrate fullstack Novel2Script pipeline
```
