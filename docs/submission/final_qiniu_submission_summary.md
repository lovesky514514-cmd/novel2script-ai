# 七牛云比赛最终提交说明

生成时间：2026-06-07 14:15:36

## 提交入口

```text
hr.qiniu.com
```

最终只提交代码仓库地址。Demo 视频链接、线上地址和说明文档放在仓库 README 中。

## 作品方向

题目三：AI 小说转剧本工具。

## 线上地址

```text
https://n2s.cc.cd
```

## Demo 视频

请在根目录 `README.md` 中替换：

```text
Demo 视频链接：请在提交前替换为可直接在线观看的公开视频链接
```

视频链接必须可直接在线观看，不要设置下载门槛或网盘登录门槛。

## 重点成果

```text
1. 支持 3 个章节以上小说文本转换为结构化剧本。
2. 支持 YAML / TXT 输出。
3. 提供 YAML Schema 文档：docs/yaml_schema.md。
4. 提供演示小说和最终生成结果：docs/demo_samples/。
5. 已上线在线演示网站：https://n2s.cc.cd。
6. 已加入后端质量守卫，减少场景串场和对白归属错误。
7. 已加入用户反馈模块和手机端适配补丁。
```

## Demo 样例文件

```text
docs/demo_samples/雨夜的信_source.txt
docs/demo_samples/雨夜的信_final_generated.txt
docs/demo_samples/雨夜的信_final_generated.yaml
```

## 最终 main 分支建议

将最终功能分支合并到：

```text
main
```

提交信息建议：

```text
fix: improve scene and dialogue quality guard
```

## 提交前检查

```text
[ ] README.md 中已经放入可直接在线观看的 Demo 视频链接
[ ] 代码仓库将于 6月8日 00:00 起设为公开
[ ] 仓库内没有 .env / API Key / 账号密码
[ ] docs/yaml_schema.md 已存在
[ ] docs/demo_samples/ 中有小说、TXT 结果和 YAML 结果
[ ] 线上地址 https://n2s.cc.cd 可访问
[ ] main 分支是最终版本
```
