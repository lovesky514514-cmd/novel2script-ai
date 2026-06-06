# Novel2Script AI YAML Schema 设计文档

## 1. 设计目标

本项目需要将 3 个章节以上的小说文本自动转换为结构化剧本 YAML。

Schema 的设计目标不是单纯让 AI 输出一份 YAML，而是让剧本具备以下能力：

1. 可读：作者可以直接阅读和修改；
2. 可编辑：每个角色、场景、对白、动作都能被单独调整；
3. 可追溯：每个剧本场景都能追溯到原小说章节和事件；
4. 可校验：程序可以检查字段是否完整、格式是否正确；
5. 可解释：能够记录模型调用链路、事实来源和修复过程；
6. 可扩展：后续可以扩展为分镜、短剧、动画、广播剧等格式。

## 2. 顶层结构

当前 YAML 顶层结构如下：

```yaml
title: ""
chapter_count: 3

memory:
  characters: []
  settings: []
  timeline: []

scenes:
  - id: "scene_001"
    title: ""
    source_chapter: 1
    source_events: []
    location: ""
    time: ""
    characters: []
    conflict: ""
    purpose: ""
    action: []
    dialogue:
      - speaker: ""
        line: ""
        emotion: ""
        subtext: ""
    notes: ""

analysis: {}

story_bible: {}

chapter_facts:
  - source_chapter: 1
    scene_title: ""
    location: ""
    time: ""
    on_stage_characters: []
    off_stage_characters: []
    key_events: []
    key_props: []
    conflict: ""
    purpose: ""
    scene_units: []

model_trace: {}

repair_questions: []

validation_report: {}

quality_report: {}
```

## 3. 字段说明

### 3.1 title

```yaml
title: ""
```

作品标题。

设计原因：

- 用于页面展示；
- 用于导出文件命名；
- 用于后续多作品管理。

### 3.2 chapter_count

```yaml
chapter_count: 3
```

原小说章节数量。

设计原因：

- 方便确认输入是否满足 3 章以上；
- 方便后续校验场景是否覆盖主要章节。

### 3.3 memory

```yaml
memory:
  characters: []
  settings: []
  timeline: []
```

用于存储小说事实记忆。

设计原因：

- 减少长文本改编时的人物遗忘；
- 保持时间线和人物关系一致；
- 为后续 `chapter_facts` 和场景生成提供背景。

### 3.4 scenes

`scenes` 是剧本主体。

```yaml
scenes:
  - id: "scene_001"
    title: ""
    source_chapter: 1
    source_events: []
    location: ""
    time: ""
    characters: []
    conflict: ""
    purpose: ""
    action: []
    dialogue:
      - speaker: ""
        line: ""
        emotion: ""
        subtext: ""
    notes: ""
```

字段设计原因：

- `id`：便于定位、修改和导出；
- `title`：便于用户快速浏览；
- `source_chapter`：确保场景能追溯到原小说章节；
- `source_events`：记录改编来源；
- `location`：满足剧本场景格式；
- `time`：满足剧本场景格式；
- `characters`：明确现场人物；
- `conflict`：保证每场戏有戏剧动力；
- `purpose`：说明本场对主线的作用；
- `action`：把小说叙述转成可表演动作；
- `dialogue`：把心理描写、冲突和信息交锋转成对白；
- `notes`：记录修复、拆场或人工确认提示。

### 3.5 story_bible

```yaml
story_bible: {}
```

用于记录全局故事信息。

可包含：

- 故事类型；
- 主线冲突；
- 人物关系；
- 关键伏笔；
- 世界观或背景设定。

设计原因：

- 避免每章单独生成时互相割裂；
- 帮助模型在长文本改编中保持一致性。

### 3.6 chapter_facts

```yaml
chapter_facts:
  - source_chapter: 1
    scene_title: ""
    location: ""
    time: ""
    on_stage_characters: []
    off_stage_characters: []
    key_events: []
    key_props: []
    conflict: ""
    purpose: ""
    scene_units: []
```

`chapter_facts` 是最终输出的事实来源，用于减少串场、地点错误、时间错误和道具污染。

字段设计原因：

- `source_chapter`：标明事实来自哪一章；
- `scene_title`：为场景标题提供依据；
- `location`：避免地点被后处理覆盖；
- `time`：避免日期中的“日”被误判为白天；
- `on_stage_characters`：区分现场人物；
- `off_stage_characters`：记录录音、短信、旁白中出现的人；
- `key_events`：保证关键事件不丢失；
- `key_props`：控制道具不串场；
- `conflict`：保证戏剧冲突；
- `purpose`：说明章节功能；
- `scene_units`：支持多地点章节拆场。

### 3.7 model_trace

```yaml
model_trace:
  provider: "deepseek"
  chat_model: "deepseek-chat"
  pro_model: "deepseek-reasoner"
  pipeline: ""
```

用于说明模型调用链路。

设计原因：

- 方便调试；
- 方便比赛展示技术路线；
- 说明系统不是单次生成，而是多阶段流程。

### 3.8 repair_questions

```yaml
repair_questions:
  - target: "scene_001"
    question: ""
    reason: ""
```

用于记录修复阶段向模型提出的问题。

设计原因：

- 让修复过程可追踪；
- 避免静默修改；
- 便于后续形成错误知识库。

### 3.9 validation_report

```yaml
validation_report:
  final_status: "pass"
  first_pass_issues: []
  repair_log: []
  final_issues: []
```

用于记录结构校验结果。

设计原因：

- 判断最终 YAML 是否通过；
- 记录初次生成的问题；
- 记录修复动作；
- 提醒用户哪些内容需要人工复查。

### 3.10 quality_report

```yaml
quality_report:
  format_valid: true
  warnings: []
```

用于记录最终输出质量状态。

设计原因：

- 给前端展示质量提示；
- 给用户提供人工确认依据；
- 给开发者提供后续优化方向。

## 4. 错误知识库关联

Schema 与 `backend/app/knowledge/error_patterns.yaml` 配合使用。

当前错误知识库主要处理：

- 日期误判为场景时间；
- 短信、录音、旁白人物误判为现场人物；
- 地点词误判为道具；
- 不同章节道具串场；
- 多地点章节强行合并；
- 旧修复日志干扰最终判断。

## 5. 可扩展方向

后续可增加：

- `shot_list`：分镜列表；
- `episode`：短剧集数；
- `duration_estimate`：时长估算；
- `visual_style`：视觉风格；
- `revision_history`：修改历史；
- `user_feedback`：用户反馈记录。
