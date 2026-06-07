from app.core.config import settings
from app.services.ai_client import AIClient
from app.version import APP_VERSION
from app.services.error_pattern_engine import load_error_patterns


def get_runtime_status():
    client = AIClient()
    api_key = getattr(client, "api_key", "") or ""
    return {
        "version": APP_VERSION,
        "app": settings.app_name,
        "env": settings.app_env,
        "provider": client.provider,
        "base_url": client.base_url,
        "chat_model": client.chat_model,
        "pro_model": client.pro_model,
        "api_key_present": bool(api_key),
        "api_key_prefix": api_key[:6] + "***" if api_key else "",
        "pipeline": "pro_learn_chat_generate_pro_validate_repair",
        "error_pattern_count": len(load_error_patterns().get("patterns", [])),
        "error_pattern_kb": "backend/app/knowledge/error_patterns.yaml",
    }
