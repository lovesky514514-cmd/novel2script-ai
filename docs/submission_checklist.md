# 比赛提交检查清单

## 1. GitHub 上传前检查

确认不要提交：

- `backend/.env`
- 真实 API Key
- `frontend/node_modules/`
- `frontend/dist/`
- `backend/logs/`
- `debug_runs/`
- 用户上传小说原文
- 真实模型响应全文

确认需要提交：

- `README.md`
- `backend/README.md`
- `docs/dev_log.md`
- `docs/reuse_statement.md`
- `docs/logging_privacy.md`
- `docs/yaml_schema.md`
- `backend/app/knowledge/error_patterns.yaml`
- 前后端源码
- `start_one_click.bat`

## 2. 分支

建议分支：

```text
feature/day2-fullstack-polish
```

## 3. Commit 信息

```text
Day 2: integrate fullstack Novel2Script pipeline
```

## 4. Pull Request 标题

```text
Day 2: Fullstack Novel2Script AI pipeline
```

## 5. Pull Request 摘要

- 完成前后端整合；
- 接入 DeepSeek API；
- 增加小说上传、生成进度、结果预览、继续修改和导出；
- 增加错误知识库和质量追踪字段；
- 补充日志、隐私、复用和比赛提交说明。
