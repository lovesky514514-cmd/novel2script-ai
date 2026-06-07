# Novel2Script AI

AI 小说转剧本工具。  
线上演示：<https://n2s.cc.cd>

> Demo 视频链接：**请在提交前替换为可直接在线观看的公开视频链接**  
> 示例：`https://...`

## 1. 项目简介

Novel2Script AI 面向小说作者和短剧创作者，支持将 3 个章节以上的小说文本自动转换为结构化剧本初稿。

核心能力：

- 上传 TXT / MD 小说文本；
- 自动拆分章节和场景；
- 输出可编辑的分场剧本；
- 支持 YAML / TXT 导出；
- 支持生成后继续修改；
- 支持用户反馈记录；
- 针对短信、录音、信件、纸条等非现场文本做对白来源保护。

## 2. 在线体验

```text
https://n2s.cc.cd
```

## 3. Demo 样例

本仓库提供一组演示样例：

```text
docs/demo_samples/
├── 雨夜的信_source.txt
├── 雨夜的信_final_generated.txt
└── 雨夜的信_final_generated.yaml
```

示例小说《雨夜的信》包含 3 个章节，覆盖：

- 雨夜旧楼；
- 匿名短信；
- 顾言重逢；
- 钥匙；
- 西港17号仓库；
- 父亲录音；
- 项目经理反转。

最终生成结果中：

- 短信内容会标记为 `短信内容`；
- 录音内容会标记为 `父亲录音`；
- 公司会议室场景不会混入旧楼动作；
- 林夏家翻找钥匙场景不会混入仓库内容；
- 项目经理台词归属正确。

## 4. YAML Schema

比赛要求的剧本 YAML Schema 文档：

```text
docs/yaml_schema.md
```

该文档说明了：

- YAML 顶层结构；
- 场景字段设计；
- 人物、地点、道具、对白和校验字段；
- 为什么要区分人物对白和短信/录音/信件等非现场来源。

## 5. 核心目录

```text
backend/
  app/
    services/
      final_result_guard.py
      character_guard.py

frontend/

docs/
  yaml_schema.md
  demo_samples/
  patches/
  submission/
```

## 6. 后端质量守卫

最终版本重点优化：

```text
backend/app/services/final_result_guard.py
backend/app/services/character_guard.py
```

解决的问题：

- 防止不同地点之间动作串场；
- 防止会议室混入旧楼动作；
- 防止林夏家翻找钥匙场景混入仓库内容；
- 防止短信内容被错误归给人物；
- 防止父亲录音被错误归给林夏或顾言；
- 保留项目经理反转台词归属。

最终质量守卫补丁位于：

```text
docs/patches/08_backend_quality_guard_final_patch/
```

## 7. 本地运行

后端：

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Windows PowerShell 可使用：

```powershell
cd backend
.\.venv\Scripts\activate
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev
```

## 8. 环境变量

请参考 `.env.example` 或自行创建后端 `.env`。  
