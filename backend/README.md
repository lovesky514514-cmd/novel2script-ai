# Novel2Script AI Backend

本目录是 Novel2Script AI 的后端服务。

当前阶段为后端初始化，仅包含基础 FastAPI 服务、健康检查接口和工作流预览接口。

## 当前接口

### 健康检查

```text
GET /health
```

### 项目状态

```text
GET /api/status
```

### 工作流预览

```text
GET /api/workflow-preview
```

## 本地启动

进入 backend 目录：

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
http://127.0.0.1:8000/api/status
http://127.0.0.1:8000/api/workflow-preview
```

## 后续计划

- 增加小说章节切分；
- 增加小说事实记忆库；
- 增加 AIClient；
- 增加 YAML Schema 校验；
- 增加准确性报告。