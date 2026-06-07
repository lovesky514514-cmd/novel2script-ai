import json
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from app.models.schemas import KnowledgeRule


RULE_DIR = Path(__file__).resolve().parents[1] / "knowledge" / "rules"


@lru_cache(maxsize=1)
def load_rules() -> List[KnowledgeRule]:
    rules: List[KnowledgeRule] = []
    for file_path in sorted(RULE_DIR.glob("*.json")):
        data = json.loads(file_path.read_text(encoding="utf-8"))
        for item in data:
            rules.append(KnowledgeRule(**item))
    return rules


def summarize_rules() -> dict:
    rules = load_rules()
    by_category: dict[str, int] = {}
    by_module: dict[str, int] = {}
    for rule in rules:
        by_category[rule.category] = by_category.get(rule.category, 0) + 1
        for module in rule.apply_when:
            by_module[module] = by_module.get(module, 0) + 1
    return {
        "total": len(rules),
        "by_category": by_category,
        "by_module": by_module,
    }


def search_rules(query: str = "", module: Optional[str] = None, limit: int = 12) -> List[KnowledgeRule]:
    rules = load_rules()
    query = (query or "").strip()

    def score(rule: KnowledgeRule) -> int:
        text = f"{rule.title} {rule.rule} {' '.join(rule.check_points)} {rule.category}"
        value = 0
        if module and module in rule.apply_when:
            value += 5
        if query and query in text:
            value += 4
        for token in query.split():
            if token and token in text:
                value += 1
        return value

    ranked = sorted(rules, key=score, reverse=True)
    if query or module:
        ranked = [rule for rule in ranked if score(rule) > 0]
    return ranked[:limit]


def get_rules_for_module(module: str, limit: int = 20) -> List[KnowledgeRule]:
    return search_rules(module=module, limit=limit)
