# Novel2Script AI YAML Schema 设计文档

## 1. 设计目标

本项目需要将 3 个章节以上的小说文本自动转换为结构化剧本 YAML。

Schema 的设计目标不是单纯让 AI 输出一份 YAML，而是让剧本具备以下能力：

1. 可读：作者可以直接阅读和修改；
2. 可编辑：每个角色、场景、对白、动作都能被单独调整；
3. 可追溯：每个剧本场景都能追溯到原小说章节和事件；
4. 可校验：程序可以检查字段是否完整、格式是否正确；
5. 可扩展：后续可以扩展为分镜、短剧、动画、广播剧等格式。

## 2. 顶层结构

推荐 YAML 顶层结构如下：

```yaml
metadata:
  title: ""
  source_chapters: 3
  adaptation_style: "screenplay"
  language: "zh-CN"
  created_by: "Novel2Script AI"

source_summary:
  global_logline: ""
  main_conflict: ""
  theme: ""

characters:
  - id: "char_001"
    name: ""
    role: "protagonist"
    traits: []
    motivation: ""
    relationships: []

memory:
  timeline: []
  foreshadows: []
  unresolved_conflicts: []

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

quality_report:
  event_coverage: 0.0
  character_consistency: 0.0
  format_valid: true
  warnings: []
```

## 3. 字段说明

### 3.1 metadata

```yaml
metadata:
  title: ""
  source_chapters: 3
  adaptation_style: "screenplay"
  language: "zh-CN"
  created_by: "Novel2Script AI"
```

设计原因：

* `title`：保存作品标题；
* `source_chapters`：记录输入小说章节数，符合题目“三个章节以上”的要求；
* `adaptation_style`：标记改编风格，例如影视剧本、短剧、广播剧；
* `language`：便于后续扩展多语言；
* `created_by`：标记生成来源。

### 3.2 source_summary

```yaml
source_summary:
  global_logline: ""
  main_conflict: ""
  theme: ""
```

设计原因：

小说转剧本时，不能只拆场景，也要保留整体故事方向。

* `global_logline`：一句话概括故事；
* `main_conflict`：明确主冲突；
* `theme`：保留作品主题，避免改编跑偏。

### 3.3 characters

```yaml
characters:
  - id: "char_001"
    name: ""
    role: "protagonist"
    traits: []
    motivation: ""
    relationships: []
```

设计原因：

长文本改编最容易出现人物遗忘、人物关系混乱和性格漂移。因此角色必须独立成表。

字段说明：

* `id`：角色唯一标识；
* `name`：角色姓名；
* `role`：角色类型，例如 protagonist、antagonist、supporting；
* `traits`：人物性格标签；
* `motivation`：角色核心动机；
* `relationships`：与其他角色的关系。

### 3.4 memory

```yaml
memory:
  timeline: []
  foreshadows: []
  unresolved_conflicts: []
```

设计原因：

小说转剧本不能只处理当前章节，还要保留长期上下文。

* `timeline`：记录事件顺序；
* `foreshadows`：记录伏笔；
* `unresolved_conflicts`：记录尚未解决的矛盾。

这部分相当于剧本改编过程中的上下文记忆，防止 AI 看后面忘前面。

### 3.5 scenes

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

设计原因：

剧本的核心是场景。每个场景必须包含地点、人物、冲突、动作和对白。

字段说明：

* `id`：场景唯一标识；
* `title`：场景标题；
* `source_chapter`：来源章节；
* `source_events`：来源事件 ID；
* `location`：场景地点；
* `time`：场景时间；
* `characters`：出场人物；
* `conflict`：本场冲突；
* `purpose`：本场在剧情中的作用；
* `action`：动作描写；
* `dialogue`：对白；
* `notes`：补充说明。

其中 `source_chapter` 和 `source_events` 是准确性控制的关键字段。它们用于证明场景来自原小说，而不是 AI 凭空生成。

### 3.6 dialogue

```yaml
dialogue:
  - speaker: ""
    line: ""
    emotion: ""
    subtext: ""
```

设计原因：

小说中的心理描写通常不能直接进入剧本，需要转化为对白、动作和潜台词。

字段说明：

* `speaker`：说话人；
* `line`：对白内容；
* `emotion`：说话情绪；
* `subtext`：潜台词。

加入 `emotion` 和 `subtext` 可以让输出更像剧本，而不是简单对话列表。

### 3.7 quality_report

```yaml
quality_report:
  event_coverage: 0.0
  character_consistency: 0.0
  format_valid: true
  warnings: []
```

设计原因：

AI 生成内容需要可检查。质量报告用于提示用户哪些部分可靠，哪些部分需要人工确认。

字段说明：

* `event_coverage`：关键事件覆盖率；
* `character_consistency`：角色一致性评分；
* `format_valid`：YAML 格式是否通过校验；
* `warnings`：需要人工确认的问题。

## 4. 准确性控制设计

为了减少 AI 幻觉，本项目要求每个场景都必须绑定：

```yaml
source_chapter: 1
source_events:
  - "event_001"
```

这意味着：

1. 每个场景都能追溯到原小说；
2. 程序可以检查是否出现无来源场景；
3. 用户可以知道哪些内容是忠实改编，哪些内容是艺术加工；
4. 后续可以生成准确性报告。

## 5. 为什么不用纯文本剧本格式

纯文本剧本虽然适合阅读，但不适合程序校验和二次处理。

YAML 的优势是：

* 结构清晰；
* 可读性比 JSON 更好；
* 能表达层级关系；
* 能被程序解析；
* 适合后续导出 Markdown、Word、分镜表等格式。

## 6. 后续扩展方向

Schema 后续可以扩展：

1. `shots`：分镜信息；
2. `camera`：镜头语言；
3. `sound`：音效和背景音乐；
4. `costume`：服装道具；
5. `duration`：场景时长；
6. `platform_style`：短剧、网剧、广播剧等平台风格。

## 7. 当前状态

当前文档为初版 Schema 设计，后续会根据功能开发和测试结果继续调整。
