# 01 用户反馈服务器上线后修改补丁执行包

生成时间：2026-06-07 05:15:27

## 这个文件夹是干什么的

用于把线上版 Novel2Script AI 的“功能页 → 用户反馈设计”改成真实用户反馈模块。

## 修改内容

- 前端：把“用户反馈设计”规划卡片替换为聊天式反馈输入框；
- 后端：新增 `POST /api/feedback`；
- 存储：反馈写入 `backend/data/feedback/feedback.jsonl`；
- 汇总：同步生成 `backend/data/feedback/feedback_report.md`；
- 安全：不往 `.env` 写入 `FEEDBACK_ADMIN_TOKEN` / `FEEDBACK_DIR`，避免 Pydantic Settings 报错。

## 服务器执行方式

把本文件夹上传到服务器，例如：

```bash
/root/01_user_feedback_online_patch
```

执行：

```bash
cd /root/01_user_feedback_online_patch
bash apply_feedback_online_patch.sh
```

## 涉及文件

```text
backend/app/api/routes.py
frontend/src/main.jsx
frontend/src/styles.css
```

## 不会修改

```text
Nginx
证书
.env
```
