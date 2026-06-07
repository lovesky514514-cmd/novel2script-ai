# Novel2Script AI Backend

后端基于 FastAPI 实现，负责小说解析、模型调用、异步任务管理、结构化 YAML 输出、生成校验和错误知识库读取。

## 主要接口

### `GET /health`

健康检查。

### `GET /api/version`

查看当前后端版本。

### `GET /api/debug/runtime`

查看运行状态、模型配置和错误知识库加载状态。

### `POST /api/convert-ai/start`

启动小说转剧本异步任务。

### `GET /api/jobs/{job_id}/status`

查看生成进度。

### `GET /api/jobs/{job_id}/result`

获取生成结果。

### `POST /api/revise-script`

根据用户补充要求继续修改剧本。

### `GET /api/schema`

查看 YAML 输出结构说明。

## 模型配置

在 `backend/.env` 中配置：

```text
AI_PROVIDER=deepseek
AI_API_KEY=你的 DeepSeek Key
AI_BASE_URL=https://api.deepseek.com/v1
AI_CHAT_MODEL=deepseek-chat
AI_PRO_MODEL=deepseek-reasoner
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
