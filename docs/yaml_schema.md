# YAML Schema

Novel2Script AI 的输出包含人类可读剧本预览和结构化 YAML 两部分。YAML 用于记录生成结果、事实来源、模型链路和质量报告。

## 顶层字段

```yaml
title: "作品标题"
chapter_count: 3
memory:
  characters: []
  settings: []
  timeline: []
scenes: []
analysis: {}
story_bible: {}
chapter_facts: []
model_trace: {}
repair_questions: []
validation_report: {}
quality_report: {}
```

## scenes

```yaml
scenes:
  - id: "scene_001"
    title: "场景标题"
    source_chapter: 1
    location: "地点"
    time: "时间"
    characters:
      - "人物"
    conflict: "本场冲突"
    action:
      - "动作描述"
    dialogue:
      - speaker: "人物"
        line: "对白"
        emotion: "情绪"
        subtext: "潜台词"
    purpose: "场景目的"
```

## chapter_facts

`chapter_facts` 是最终输出的事实来源，用于减少串场、地点错误、时间错误和道具污染。

```yaml
chapter_facts:
  - source_chapter: 1
    scene_title: "建议场景标题"
    location: "本章主要地点"
    time: "日/夜/深夜/晨/午/傍晚/-"
    on_stage_characters: []
    off_stage_characters: []
    key_events: []
    key_props: []
    conflict: "主要冲突"
    purpose: "章节功能"
    scene_units: []
```

## model_trace

`model_trace` 用于说明模型调用链路。

```yaml
model_trace:
  provider: "deepseek"
  chat_model: "deepseek-chat"
  pro_model: "deepseek-reasoner"
  pipeline: "pro_learn_chat_generate_pro_validate_repair"
```

## repair_questions

`repair_questions` 用于记录修复阶段向模型提出的问题。

```yaml
repair_questions:
  - target: "scene_001"
    question: "地点是否来自当前章节？"
    reason: "检测到地点不一致"
```

## validation_report

`validation_report` 用于记录结构校验结果。

```yaml
validation_report:
  final_status: "pass"
  first_pass_issues: []
  repair_log: []
  final_issues: []
```

## quality_report

`quality_report` 用于记录最终输出质量状态。

```yaml
quality_report:
  format_valid: true
  warnings: []
```

## 说明

- `chapter_facts` 是最终输出的事实来源；
- `validation_report` 用于记录结构校验结果；
- `quality_report` 用于记录最终输出质量；
- `model_trace` 用于说明模型调用链路；
- `repair_questions` 用于记录修复阶段的追问与判断。
