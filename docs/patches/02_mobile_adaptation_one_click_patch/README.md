# 02 手机格式适配一键部署包

生成时间：2026-06-07 05:15:27

## 这个文件夹是干什么的

用于给已经上线的 Novel2Script AI 网页做手机端适配。

## 修改内容

- 手机端首页标题、上传区尺寸压缩；
- “语音 / 发送”按钮手机端不换行；
- 结果页空状态居中；
- 功能页 01 / 02 横向自然滑动；
- 用户反馈输入框手机端适配；
- 只在 `@media (max-width: 768px)` 生效，电脑端不受影响。

## 服务器执行方式

```bash
cd /root/02_mobile_adaptation_one_click_patch
bash apply_mobile_adaptation_patch.sh
```

## 涉及文件

```text
frontend/src/styles.css
```

## 不会修改

```text
backend
Nginx
证书
.env
skyzhiyi.cc.cd
```
