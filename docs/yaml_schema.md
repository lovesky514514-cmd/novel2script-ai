# Novel2Script AI 剧本 YAML Schema 说明

Novel2Script AI 的输出包含人类可读剧本预览和结构化 YAML 两部分。YAML 用于记录生成结果、事实来源、模型链路和质量报告。

本 Schema 用于把 3 个章节以上的小说文本转换为结构化剧本初稿。设计目标是：

- 让作者快速看到“小说内容如何被拆成可拍摄场景”；
- 保留人物、地点、时间、道具、动作、对白和场景目的；
- 支持后续人工继续修改、导出、分镜或拍摄流程衔接；
- 让生成结果具备可校验性，减少地点串场、对白归属错误和关键线索丢失。

## 2. 顶层结构

```yaml
meta:
  title: string
  source_type: novel
  generated_at: string
  version: string

story_bible:
  characters:
    - name: string
      role: string
      description: string
  key_locations:
    - name: string
      description: string
  key_props:
    - name: string
      description: string
  core_conflict: string

```yaml
scenes:
  - scene_id: integer
    title: string
    chapter_ref: string
    location: string
    time: string
    characters:
      - string
    conflict: string
    action:
      - string
    props:
      - string
    dialogue:
      - speaker: string
        line: string
        emotion: string
        subtext: string
    purpose: string
    validation:
      status: pass | needs_review
      warnings:
        - string

exports:
  txt_available: boolean
  yaml_available: boolean
```

## chapter_facts

### meta

记录生成文件的基础信息，便于区分不同小说、不同版本和不同生成时间。

### story_bible

用于保存全局设定，包括人物、地点、道具和核心冲突。  
设计原因：小说转剧本时最容易出现人物关系混乱和线索丢失，story_bible 可以作为后续场景生成和校验的统一参考。

### scenes

剧本主体。每个 scene 对应一个可编辑、可拍摄的场景单元。

#### scene_id

场景编号，便于作者定位和修改。

#### title

场景标题，用于快速判断本场内容。

#### chapter_ref

原小说章节来源，便于回查原文。

#### location

场景地点。  
设计原因：地点是防止动作串场的关键字段。例如“公司会议室”不应混入“旧楼楼道”的动作。

#### time

场景时间，如“夜”“上午”“深夜”。  
设计原因：短剧和影视剧本需要明确时间环境，便于拍摄和剪辑。

#### characters

本场出现人物列表。  
设计原因：对白说话人必须来自本场人物，或来自短信、录音、信件等非现场来源。

#### conflict

本场核心冲突。  
设计原因：每场戏都应有目标和阻碍，避免只是复述小说内容。

#### action

可拍摄动作列表。  
设计原因：小说描写需要转化为镜头和演员动作，action 字段用于承接这一转换。

#### props

本场关键道具。  
设计原因：悬疑、短剧和改编剧本中，道具经常承担伏笔作用，如短信、信封、照片、钥匙、录音笔等。

#### dialogue

对白列表，每条对白包含：

```yaml
speaker: string
line: string
emotion: string
subtext: string
```

设计原因：

- speaker 保证说话人清晰；
- line 保存台词内容；
- emotion 帮助演员理解情绪；
- subtext 保存潜台词或信息来源。

对于短信、录音、信件、纸条、屏幕文字等非现场来源，speaker 可写为：

```yaml
短信内容
父亲录音
录音声
信件内容
纸条内容
屏幕文字
旁白
```

这样可以避免把非人物文本错误归给现场角色。

#### purpose

本场作用，如“引出钥匙”“揭示反派”“制造悬念”。  
设计原因：方便作者判断每场是否有必要保留。

#### validation

保存质量检查结果。  
设计原因：AI 生成内容可能出现地点串场、对白归属错误、道具遗漏等问题，validation 用于提示作者复核。

## 4. 示例片段

```yaml
scenes:
  - scene_id: 6
    title: 仓库对峙
    chapter_ref: 第三章 钥匙
    location: 西港17号仓库
    time: 深夜
    characters:
      - 林夏
      - 顾言
      - 项目经理
    conflict: 林夏得知父亲让顾言隐瞒真相，项目经理现身证实幕后操纵。
    action:
      - 林夏到达仓库，顾言已等候。
      - 林夏展示钥匙，顾言称这不是父亲的钥匙。
      - 两人打开铁门，发现保险箱、录音笔和旧手机。
    props:
      - 钥匙
      - 保险箱
      - 录音笔
      - 旧手机
      - 项目经理的钥匙
    dialogue:
      - speaker: 项目经理
        line: 录音还是被你们找到了。
        emotion: 冷静
        subtext: 反派身份开始浮出水面。
      - speaker: 父亲录音
        line: 林夏，如果你听到这段录音，说明我可能已经回不去了。
        emotion: 沉重
        subtext: 来自录音，不是现场人物对白。
    purpose: 揭示关键录音内容，引出幕后操纵者。
    validation:
      status: pass
      warnings: []
```

## 5. Schema 设计原因总结

本 Schema 不是只保存“生成文本”，而是把剧本拆成可编辑的数据结构：

- `story_bible` 负责全局一致性；
- `scenes` 负责剧本主体；
- `location / characters / props` 用于防止串场；
- `dialogue.speaker` 区分人物对白和非现场来源；
- `validation` 支持后续质量检查和人工复核。

这样可以让小说作者快速获得一个可继续打磨的剧本初稿，而不是只能复制一段不可控的 AI 文本。
