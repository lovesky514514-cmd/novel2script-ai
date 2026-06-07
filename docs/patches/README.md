# 线上部署后补丁包说明

生成时间：2026-06-07 05:23:51

本目录是在原始本地跑通包 `novel2script-ai` 的基础上追加的线上部署后补丁文件。

```text
docs/patches/
├── 01_user_feedback_online_patch/
├── 02_mobile_adaptation_one_click_patch/
└── 03_wechat_miniprogram_deploy_package/
```

## 01_user_feedback_online_patch

用户反馈服务器上线后修改补丁一键执行包。

用途：

- 把功能页“用户反馈设计”替换成真实反馈输入框；
- 新增后端 `POST /api/feedback`；
- 把反馈保存到服务器文件；
- 生成 Markdown 反馈文档。

## 02_mobile_adaptation_one_click_patch

手机格式适配一键部署包。

用途：

- 手机端页面适配；
- 首页标题、按钮、上传框适配；
- 结果页居中；
- 功能页卡片横滑；
- 只影响手机端，不影响电脑端。

## 03_wechat_miniprogram_deploy_package

微信小程序部署包。

用途：

- 小程序 web-view 承载 `https://n2s.cc.cd`；
- 用于微信开发者工具导入和演示；
- 不包含版权图片或第三方素材。
