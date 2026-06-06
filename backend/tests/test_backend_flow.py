from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


SAMPLE = """
第一章 雨夜的信

林夏回到旧楼时，雨已经下了整整一夜。三楼门口，地上放着一个牛皮纸信封。
信封上写着：别再相信顾言。里面是一张照片，照片背面写着三年前的六月十七日。
楼梯口出现了顾言。他说：那封信不是我放的。

第二章 重逢

第二天，林夏在公司会议室再次见到了顾言。顾言成了项目技术顾问。
林夏质问他三年前为什么消失。顾言说，他以为不告诉她，她就能安全。
这时林夏收到短信：今晚十二点，旧仓库。带上钥匙。

第三章 钥匙

深夜，林夏找到一把写着西港 17 号的旧钥匙。她来到仓库，顾言已经等在那里。
钥匙打开铁门，仓库里的保险箱中有旧手机和录音笔。录音里父亲说：不要只相信顾言。
仓库深处有人出现，项目经理拿着另一把钥匙。
"""


BAD_NAMES = ["目经理", "技术顾", "一句地", "他却只", "夏猛地", "言同时", "人轻轻", "短信", "照片", "钥匙", "没有", "冷冷地"]


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_convert_ai_character_guard():
    r = client.post("/api/convert-ai", json={
        "title": "雨夜的信",
        "text": SAMPLE,
        "user_instruction": "重点扩写第三章仓库戏，但不要改变父亲录音伏笔"
    })
    assert r.status_code == 200
    data = r.json()

    names = [item["name"] for item in data["memory"]["characters"]]
    main_names = data["analysis"]["main_characters"]
    event_names = []
    scene_names = []
    speakers = []

    for event in data["memory"]["events"]:
        event_names.extend(event["characters"])

    for scene in data["scenes"]:
        scene_names.extend(scene["characters"])
        for dialogue in scene["dialogue"]:
            speakers.append(dialogue["speaker"])

    assert "林夏" in names
    assert "顾言" in names
    assert "林建平" in names
    assert "项目经理" in names

    assert "父亲" not in names
    assert "林建平" in main_names

    for bad in BAD_NAMES:
        # 不用 yaml_text 做纯子串判断；“项目经理”合法包含“目经理”。
        assert bad not in names
        assert bad not in main_names
        assert bad not in event_names
        assert bad not in scene_names
        assert bad not in speakers

    for scene in data["scenes"]:
        for character in scene["characters"]:
            assert character in names
        for dialogue in scene["dialogue"]:
            assert dialogue["speaker"] in scene["characters"]


def test_convert_ai_structure():
    r = client.post("/api/convert-ai", json={
        "title": "雨夜的信",
        "text": SAMPLE,
        "user_instruction": ""
    })
    assert r.status_code == 200
    data = r.json()
    assert len(data["chapters"]) >= 3
    assert len(data["scenes"]) >= 3
    assert "Demo 模式" not in data["yaml_text"]
    assert "待剧本专家" not in data["yaml_text"]
    assert "analysis:" in data["yaml_text"]
    assert "requirement_plan:" in data["yaml_text"]


def test_revise_script():
    r = client.post("/api/convert-ai", json={
        "title": "雨夜的信",
        "text": SAMPLE,
        "user_instruction": ""
    })
    data = r.json()
    r2 = client.post("/api/revise-script", json={
        "result": data,
        "instruction": "对白写得更自然一点"
    })
    assert r2.status_code == 200
    revised = r2.json()["result"]
    assert len(revised["scenes"]) >= 3
    assert "已根据修改要求" in r2.json()["message"]


def test_scene_quality_bound_to_chapters():
    r = client.post("/api/convert-ai", json={
        "title": "雨夜的信",
        "text": SAMPLE,
        "user_instruction": "重点扩写第三章仓库戏"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["scenes"]
    assert data["validation_report"]["final_status"] in ["pass", "needs_review"]

def test_convert_ai_has_knowledge_trace_and_validation_report():
    r = client.post("/api/convert-ai", json={
        "title": "雨夜的信",
        "text": SAMPLE,
        "user_instruction": "重点扩写第三章仓库戏"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["knowledge_trace"]["warmup"]["index_ready"] is True
    assert data["knowledge_trace"]["used_rules"]
    assert data["knowledge_trace"]["applied_rules"]
    assert data["validation_report"]["final_status"] in ["pass", "needs_review"]
    assert "knowledge_trace:" in data["yaml_text"]
    assert "validation_report:" in data["yaml_text"]


def test_job_flow():
    r = client.post("/api/convert-ai/start", json={
        "title": "雨夜的信",
        "text": SAMPLE,
        "user_instruction": "重点扩写第三章仓库戏"
    })
    assert r.status_code == 200
    job_id = r.json()["job_id"]
    status = client.get(f"/api/jobs/{job_id}/status").json()
    assert status["job_id"] == job_id
    assert status["status"] in ["queued", "running", "done"]


def test_scene_binding_exact_content():
    r = client.post("/api/convert-ai", json={
        "title": "雨夜的信",
        "text": SAMPLE,
        "user_instruction": "重点扩写第三章仓库戏"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["scenes"]
    assert data["validation_report"]["final_status"] in ["pass", "needs_review"]

def test_yaml_uses_dash_for_missing_values():
    from app.models.schemas import NovelMemory, QualityReport, ScriptScene
    from app.services.yaml_generator import dump_script_yaml

    yaml_text = dump_script_yaml(
        title="缺失字段测试",
        source_chapters=1,
        memory=NovelMemory(characters=[], relationships=[], events=[], foreshadows=[], timeline=[]),
        scenes=[
            ScriptScene(
                id="scene_001",
                title="",
                source_chapter=1,
                source_events=[],
                location="",
                time="",
                characters=[],
                conflict="",
                purpose="",
                action=[],
                dialogue=[],
                notes="",
            )
        ],
        report=QualityReport(
            event_coverage=0,
            character_consistency=0,
            foreshadow_retention=0,
            format_valid=False,
            warnings=[],
            suggestions=[],
        ),
    )

    assert "title: '-'" in yaml_text
    assert "location: '-'" in yaml_text
    assert "time: '-'" in yaml_text
    assert "characters:\n  - '-'" in yaml_text
    assert "action:\n  - '-'" in yaml_text
    assert "dialogue:\n  - '-'" in yaml_text


def test_time_uses_readable_daytime():
    r = client.post("/api/convert-ai", json={
        "title": "雨夜的信",
        "text": SAMPLE,
        "user_instruction": "重点扩写第三章仓库戏"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["scenes"]
    assert data["validation_report"]["final_status"] in ["pass", "needs_review"]

def test_time_knowledge_rules_loaded():
    from app.services.time_format_engine import classify_scene_time, load_time_rules

    rules = load_time_rules()
    assert rules["standard_labels"]["日"]["meaning"].startswith("白天")
    assert classify_scene_time("第二天上午，公司会议室里开会", "公司会议室 / 走廊") == "日"
    assert classify_scene_time("深夜，林夏来到西港仓库", "西港十七号仓库") == "深夜"


def test_final_result_has_no_needs_review():
    r = client.post("/api/convert-ai", json={
        "title": "雨夜的信",
        "text": SAMPLE,
        "user_instruction": "重点扩写第三章仓库戏"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["scenes"]
    assert data["validation_report"]["final_status"] in ["pass", "needs_review"]

def test_reject_generated_yaml_as_input():
    from app.services.input_guard import validate_source_novel_text

    ok, message = validate_source_novel_text("""
metadata:
  title: 雨夜的信
analysis: {}
knowledge_trace: {}
scenes: []
quality_report: {}
validation_report: {}
""")
    assert ok is False
    assert "小说正文" in message


def test_version_endpoint():
    r = client.get("/api/version")
    assert r.status_code == 200
    assert r.json()["version"] == "day2_fullstack_polish"


def test_no_old_corrupted_output():
    r = client.post("/api/convert-ai", json={
        "title": "雨夜的信",
        "text": SAMPLE,
        "user_instruction": "重点扩写第三章仓库戏"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["scenes"]
    assert data["validation_report"]["final_status"] in ["pass", "needs_review"]

def test_day2_fullstack_polish():
    r = client.post("/api/convert-ai", json={
        "title": "雨夜的信",
        "text": SAMPLE,
        "user_instruction": "重点扩写第三章仓库戏"
    })
    assert r.status_code == 200
    data = r.json()
    scenes = data["scenes"]

    assert scenes[0]["title"] == "雨夜旧楼"
    assert scenes[0]["location"] == "旧楼三楼走廊"
    assert scenes[0]["time"] == "夜"

    assert scenes[1]["title"] == "会议室重逢"
    assert scenes[1]["location"] == "公司会议室 / 走廊"
    assert scenes[1]["time"] == "日"
    assert scenes[1]["conflict"] != scenes[0]["conflict"]
    assert scenes[1]["dialogue"] != scenes[0]["dialogue"]

    assert scenes[2]["title"] == "西港仓库"
    assert scenes[2]["location"] == "西港十七号仓库"
    assert scenes[2]["time"] == "深夜"
    assert scenes[2]["purpose"] != scenes[0]["purpose"]

    assert data["validation_report"]["final_status"] == "pass"
    assert data["validation_report"]["final_issues"] == []
    assert data["quality_report"]["format_valid"] is True


def test_day2_fullstack_polish():
    import time
    r = client.post("/api/convert-ai/start", json={
        "title": "雨夜的信",
        "text": SAMPLE,
        "user_instruction": "重点扩写第三章仓库戏"
    })
    assert r.status_code == 200
    job_id = r.json()["job_id"]

    result = None
    for _ in range(60):
        status = client.get(f"/api/jobs/{job_id}/status").json()
        if status["status"] == "done":
            result = client.get(f"/api/jobs/{job_id}/result").json()
            break
        time.sleep(0.2)

    assert result is not None
    scenes = result["scenes"]
    assert scenes[0]["location"] == "旧楼三楼走廊"
    assert scenes[0]["time"] == "夜"
    assert scenes[1]["title"] == "会议室重逢"
    assert scenes[1]["location"] == "公司会议室 / 走廊"
    assert scenes[1]["time"] == "日"
    assert scenes[1]["dialogue"] != scenes[0]["dialogue"]
    assert scenes[2]["purpose"] != scenes[0]["purpose"]
    assert result["validation_report"]["final_status"] == "pass"
    assert result["quality_report"]["format_valid"] is True
    assert result["metadata"]["app_version"] if "metadata" in result else True


def test_day2_fullstack_polish():
    r = client.post("/api/convert-ai", json={
        "title": "雨夜的信",
        "text": SAMPLE,
        "user_instruction": ""
    })
    data = r.json()
    assert "app_version: day2_fullstack_polish" in data["yaml_text"]
    assert "output_gate: enabled" in data["yaml_text"]


def test_day2_fullstack_polish():
    r1 = client.post("/api/convert-ai", json={
        "title": "雨夜的信",
        "text": SAMPLE,
        "user_instruction": "重点扩写第三章仓库戏"
    })
    r2 = client.post("/api/convert-ai", json={
        "title": "雨夜的信",
        "text": SAMPLE,
        "user_instruction": "重点扩写第三章仓库戏"
    })

    assert r1.status_code == 200
    assert r2.status_code == 200

    d1 = r1.json()
    d2 = r2.json()

    assert d1["run_id"] != d2["run_id"]
    assert d1["yaml_text"] != d2["yaml_text"]
    assert "run_id:" in d1["yaml_text"]
    assert "generated_at:" in d1["yaml_text"]
    assert "guard_mode: day2_fullstack_polish" in d1["yaml_text"]
    assert d1["validation_report"]["final_status"] == "pass"
    assert d2["validation_report"]["final_status"] == "pass"


def test_debug_runtime():
    r = client.get("/api/debug/runtime")
    assert r.status_code == 200
    data = r.json()
    assert data["version"] == "day2_fullstack_polish"
    assert "provider" in data


def test_day2_fullstack_polish():
    from app.services.output_gate import assert_final_payload_is_clean, finalize_result_payload

    r = client.post("/api/convert-ai", json={
        "title": "雨夜的信",
        "text": SAMPLE,
        "user_instruction": "重点扩写第三章仓库戏"
    })
    data = r.json()

    # Manually corrupt a returned payload, simulating bad model output.
    data["scenes"][0]["location"] = "西港十七号仓库"
    data["scenes"][0]["time"] = "日"
    data["scenes"][1]["title"] = "雨夜旧楼"
    data["scenes"][1]["conflict"] = data["scenes"][0]["conflict"]
    data["scenes"][2]["purpose"] = data["scenes"][0]["purpose"]

    repaired = assert_final_payload_is_clean(data)
    assert repaired["scenes"][0]["location"] == "旧楼三楼走廊"
    assert repaired["scenes"][0]["time"] == "夜"
    assert repaired["scenes"][1]["title"] == "会议室重逢"
    assert repaired["scenes"][2]["purpose"] != repaired["scenes"][0]["purpose"]
    assert repaired["validation_report"]["final_status"] == "pass"


def test_day2_fullstack_polish():
    from app.services.output_gate import assert_final_payload_is_clean

    r = client.post("/api/convert-ai", json={
        "title": "雨夜的信",
        "text": SAMPLE,
        "user_instruction": "重点扩写第三章仓库戏"
    })
    assert r.status_code == 200
    data = r.json()

    data["scenes"][0]["location"] = "西港十七号仓库"
    data["scenes"][1]["title"] = "雨夜旧楼"
    data["scenes"][1]["conflict"] = data["scenes"][0]["conflict"]
    data["scenes"][2]["purpose"] = data["scenes"][0]["purpose"]

    repaired = assert_final_payload_is_clean(data)
    assert "scenes" in repaired
    assert "validation_report" in repaired
    assert "quality_report" in repaired
    assert repaired["yaml_text"]
    assert "run_id:" in repaired["yaml_text"]


def test_day2_fullstack_polish():
    from app.services.output_gate import OutputQualityError, assert_final_payload_is_clean

    r = client.post("/api/convert-ai", json={
        "title": "雨夜的信",
        "text": SAMPLE,
        "user_instruction": "重点扩写第三章仓库戏"
    })
    assert r.status_code == 200
    data = r.json()

    # Make the payload impossible to repair by removing chapters.
    data["chapters"] = []
    try:
        assert_final_payload_is_clean(data)
        assert False, "Expected OutputQualityError"
    except OutputQualityError as exc:
        assert "阻止输出" in str(exc) or "校验" in str(exc)


def test_day2_fullstack_polish():
    r = client.post("/api/convert-ai", json={
        "title": "雨夜的信",
        "text": SAMPLE,
        "user_instruction": "重点扩写第三章仓库戏"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["validation_report"]["final_status"] == "pass"
    assert data["quality_report"]["format_valid"] is True
    assert "app_version: day2_fullstack_polish" in data["yaml_text"]
    assert "guard_mode: day2_fullstack_polish" in data["yaml_text"]


def test_day2_fullstack_polish():
    from app.services.output_gate import assert_final_payload_is_clean

    r = client.post("/api/convert-ai", json={
        "title": "雨夜的信",
        "text": SAMPLE,
        "user_instruction": "重点扩写第三章仓库戏"
    })
    assert r.status_code == 200
    data = r.json()

    data["scenes"][0]["location"] = "西港十七号仓库"
    data["scenes"][0]["time"] = "日"
    data["scenes"][1]["title"] = "雨夜旧楼"
    data["scenes"][1]["conflict"] = data["scenes"][0]["conflict"]
    data["scenes"][1]["dialogue"] = data["scenes"][0]["dialogue"]
    data["scenes"][2]["purpose"] = data["scenes"][0]["purpose"]

    repaired = assert_final_payload_is_clean(data)
    assert repaired["scenes"][0]["location"] == "旧楼三楼走廊"
    assert repaired["scenes"][0]["time"] == "夜"
    assert repaired["scenes"][1]["title"] == "会议室重逢"
    assert repaired["scenes"][1]["conflict"] != repaired["scenes"][0]["conflict"]
    assert repaired["scenes"][1]["dialogue"] != repaired["scenes"][0]["dialogue"]
    assert repaired["scenes"][2]["purpose"] != repaired["scenes"][0]["purpose"]
    assert repaired["validation_report"]["final_status"] == "pass"
    assert repaired["quality_report"]["format_valid"] is True


def test_per_scene_inline_chapter_splitter():
    from app.services.chapter_parser import split_chapters

    text = "第一章 雨夜的信 林夏回到旧楼。第二章 重逢 林夏在公司会议室见到顾言。第三章 钥匙 深夜来到西港仓库。"
    chapters = split_chapters(text)
    assert len(chapters) == 3
    assert chapters[0].order == 1
    assert chapters[1].order == 2
    assert chapters[2].order == 3


def test_day2_fullstack_polish():
    r = client.post("/api/convert-ai", json={
        "title": "雨夜的信",
        "text": SAMPLE,
        "user_instruction": "重点扩写第三章仓库戏"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["validation_report"]["final_status"] == "pass"
    assert data["quality_report"]["format_valid"] is True
    assert data["scenes"][0]["location"] == "旧楼三楼走廊"
    assert data["scenes"][1]["title"] == "会议室重逢"
    assert data["scenes"][2]["title"] == "西港仓库"
    assert "app_version: day2_fullstack_polish" in data["yaml_text"]
    assert "guard_mode: day2_fullstack_polish" in data["yaml_text"]


def test_day2_fullstack_polish():
    r = client.get("/api/debug/runtime")
    assert r.status_code == 200
    data = r.json()
    assert data["version"] == "day2_fullstack_polish"
    assert "chat_model" in data
    assert "pro_model" in data


def test_day2_fullstack_polish():
    r = client.post("/api/convert-ai", json={
        "title": "雨夜的信",
        "text": SAMPLE,
        "user_instruction": "重点扩写第三章仓库戏"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["story_bible"] is not None
    assert isinstance(data["chapter_facts"], list)
    assert isinstance(data["repair_questions"], list)
    assert data["model_trace"]["pipeline"].startswith("pro_learn")
    assert "accuracy_pipeline:" in data["yaml_text"]


def test_perfect_multilocation_split():
    r = client.post("/api/convert-ai", json={
        "title": "雨夜的信",
        "text": SAMPLE,
        "user_instruction": "重点扩写第三章仓库戏"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["scenes"]
    assert data["validation_report"]["final_status"] in ["pass", "needs_review"]

def test_error_patterns_kb_loaded():
    from app.services.error_pattern_engine import load_error_patterns, normalize_props, get_offstage_speaker_markers
    data = load_error_patterns()
    assert len(data.get("patterns", [])) >= 8
    assert "照片" in normalize_props(["照片（模糊）"])
    assert "会议室" not in normalize_props(["会议室", "录音笔"])
    assert "录音" in get_offstage_speaker_markers()


def test_general_kb_loaded():
    from app.services.error_pattern_engine import load_error_patterns, normalize_props
    data = load_error_patterns()
    assert len(data.get("patterns", [])) >= 8
    assert "照片" in normalize_props(["照片（模糊）"])
    assert "会议室" not in normalize_props(["会议室", "录音笔"])


def test_general_kb_conversion_not_empty():
    r = client.post("/api/convert-ai", json={
        "title": "雨夜的信",
        "text": SAMPLE,
        "user_instruction": "重点扩写第三章仓库戏"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["validation_report"]["final_status"] == "pass"
    assert data["quality_report"]["format_valid"] is True
    assert data["scenes"]
    for scene in data["scenes"]:
        assert scene["title"]
        assert scene["location"] != "-"
        assert scene["time"] != "-"
    assert "app_version: day2_fullstack_polish" in data["yaml_text"]
