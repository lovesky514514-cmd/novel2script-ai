import re
from typing import List

from app.models.schemas import Chapter


LINE_CHAPTER_PATTERN = re.compile(
    r"(?m)^\s*(第\s*[一二三四五六七八九十百千万0-9]+\s*章[^\n]*|Chapter\s+\d+[^\n]*|CHAPTER\s+\d+[^\n]*|[一二三四五六七八九十0-9]+[、.．]\s*[^\n]{0,40})\s*$",
    re.IGNORECASE,
)

INLINE_CHAPTER_PATTERN = re.compile(
    r"(第\s*[一二三四五六七八九十百千万0-9]+\s*章\s*[^第\n]{0,30})",
    re.IGNORECASE,
)


def _build_chapters_from_matches(cleaned: str, matches: List[re.Match]) -> List[Chapter]:
    chapters: List[Chapter] = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(cleaned)
        block = cleaned[start:end].strip()
        title = match.group(1).strip() if match.groups() else match.group(0).strip()

        if "\n" in block:
            first_line, _, body = block.partition("\n")
            if len(first_line.strip()) <= 80:
                title = first_line.strip()
                chapter_text = body.strip() or block
            else:
                chapter_text = block.replace(title, "", 1).strip() or block
        else:
            chapter_text = block.replace(title, "", 1).strip() or block

        chapters.append(
            Chapter(
                id=f"chapter_{i + 1:03d}",
                title=title,
                order=i + 1,
                text=chapter_text,
                word_count=len(chapter_text),
            )
        )
    return chapters


def split_chapters(text: str) -> List[Chapter]:
    cleaned = (text or "").strip()
    if not cleaned:
        return []

    line_matches = list(LINE_CHAPTER_PATTERN.finditer(cleaned))
    if len(line_matches) >= 2:
        return _build_chapters_from_matches(cleaned, line_matches)

    inline_matches = list(INLINE_CHAPTER_PATTERN.finditer(cleaned))
    if len(inline_matches) >= 2:
        return _build_chapters_from_matches(cleaned, inline_matches)

    markers = []
    for marker in ["第一章", "第二章", "第三章", "第四章", "第五章", "第1章", "第2章", "第3章", "第4章", "第5章"]:
        pos = cleaned.find(marker)
        if pos >= 0:
            markers.append((pos, marker))
    markers = sorted(set(markers))
    if len(markers) >= 2:
        chapters: List[Chapter] = []
        for i, (pos, marker) in enumerate(markers):
            end = markers[i + 1][0] if i + 1 < len(markers) else len(cleaned)
            block = cleaned[pos:end].strip()
            first = block.splitlines()[0].strip() if "\n" in block else marker
            title = first[:80] or marker
            body = block.replace(title, "", 1).strip() if title != marker else block.replace(marker, "", 1).strip()
            chapters.append(
                Chapter(
                    id=f"chapter_{i + 1:03d}",
                    title=title,
                    order=i + 1,
                    text=body or block,
                    word_count=len(body or block),
                )
            )
        return chapters

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", cleaned) if p.strip()]
    if len(paragraphs) >= 3:
        return [
            Chapter(
                id=f"chapter_{i:03d}",
                title=f"第 {i} 章",
                order=i,
                text=paragraph,
                word_count=len(paragraph),
            )
            for i, paragraph in enumerate(paragraphs, start=1)
        ]

    return [
        Chapter(id="chapter_001", title="未识别章节", order=1, text=cleaned, word_count=len(cleaned))
    ]



def validate_min_chapters(chapters: List[Chapter], minimum: int = 3) -> tuple[bool, str]:
    if len(chapters) < minimum:
        return False, f"当前识别到 {len(chapters)} 个章节，建议检查章节标题或换行。"
    return True, f"已识别到 {len(chapters)} 个章节。"
