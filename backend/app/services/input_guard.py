import re


def looks_like_generated_yaml(text: str) -> bool:
    sample = (text or "").strip()[:3000]
    if not sample:
        return False

    yaml_markers = [
        "metadata:",
        "analysis:",
        "knowledge_trace:",
        "validation_report:",
        "quality_report:",
        "scenes:",
    ]
    count = sum(1 for marker in yaml_markers if marker in sample)
    return count >= 3


def validate_source_novel_text(text: str) -> tuple[bool, str]:
    if looks_like_generated_yaml(text):
        return False, "请上传小说正文，不要把生成后的 YAML 结果再次作为输入。"

    clean = re.sub(r"\s+", "", text or "")
    if len(clean) < 80:
        return False, "小说正文过短，建议上传至少 3 章文本。"

    return True, ""
