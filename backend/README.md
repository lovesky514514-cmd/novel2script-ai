# Novel2Script AI Backend

本目录是 Novel2Script AI 的后端服务。

后端基于 FastAPI 实现，负责小说解析、模型调用、异步任务管理、结构化 YAML 输出、生成校验和错误知识库读取。

## 当前接口

### 健康检查

```text
GET /health
```

### 后端版本

```text
GET /api/version
```

### 运行状态

```text
GET /api/debug/runtime
```

用于查看当前后端版本、模型配置、错误知识库加载状态等调试信息。

### YAML Schema

```text
GET /api/schema
```

用于查看当前结构化输出字段说明。

### 启动小说转剧本任务

```text
POST /api/convert-ai/start
```

用于提交小说文本和用户补充要求，并启动异步生成任务。

### 查询任务进度

```text
GET /api/jobs/{job_id}/status
```

用于查询生成进度、当前阶段和任务状态。

### 获取生成结果

```text
GET /api/jobs/{job_id}/result
```

用于获取最终剧本、YAML 文本、质量报告和模型追踪字段。

### 继续修改剧本

```text
POST /api/revise-script
```

用于根据用户补充要求继续修改已生成剧本。

## 本地启动

推荐直接在项目根目录使用：

```text
start_one_click.bat
```

如果只启动后端，可以进入 backend 目录：

```bash
cd backend
```

创建虚拟环境：

```bash
python -m venv .venv
```

激活虚拟环境。

Windows PowerShell：

```bash
.venv\Scripts\Activate.ps1
```

安装依赖：

```bash
pip install -r requirements.txt
```

启动服务：

```bash
uvicorn main:app --reload
```

启动后访问：

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/api/version
http://127.0.0.1:8000/api/debug/runtime
```

## 模型配置

在 `backend/.env` 中配置：

```text
AI_PROVIDER=deepseek
AI_API_KEY=你的 DeepSeek Key
AI_BASE_URL=https://api.deepseek.com/v1
AI_CHAT_MODEL=deepseek-chat
AI_PRO_MODEL=deepseek-reasoner
```

公开仓库中不要提交真实 API Key。

## 后端工作流

```text
输入小说文本
↓
章节切分
↓
基础人物 / 事件 / 场景抽取
↓
Pro 模型抽取 story_bible / chapter_facts
↓
Chat 模型生成分场剧本
↓
Final Guard 绑定 chapter_facts
↓
validation_report / quality_report
↓
YAML 输出
```

## 质量追踪字段

后端输出中包含：

- `model_trace`
- `chapter_facts`
- `repair_questions`
- `validation_report`
- `quality_report`

这些字段用于调试和质量改进，不应作为真实用户日志公开上传。

## 隐私规则

不要提交：

- `backend/.env`
- `backend/logs/`
- `debug_runs/`
- 用户上传小说原文
- 真实模型响应全文
