from typing import Any, Dict

from app.models.schemas import ConvertResult
from app.services.final_result_guard import enforce_final_result


class OutputQualityError(RuntimeError):
    pass


def finalize_result_payload(payload: Any) -> Dict[str, Any]:
    if isinstance(payload, ConvertResult):
        result = payload
    else:
        result = ConvertResult(**payload)
    result = enforce_final_result(result)
    return result.model_dump()


def assert_final_payload_is_clean(payload: Dict[str, Any]) -> Dict[str, Any]:
    final_payload = finalize_result_payload(payload)
    # Do not return totally malformed data.
    if not final_payload.get("scenes"):
        raise OutputQualityError("没有生成 scenes。")
    if "run_id:" not in (final_payload.get("yaml_text") or ""):
        raise OutputQualityError("结果缺少 run_id。")
    return final_payload
