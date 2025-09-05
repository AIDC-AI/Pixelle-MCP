import requests
from urllib.parse import urljoin
from typing import List


def check_url_status(url: str, timeout: int = 5) -> bool:
    """Return True if the URL is reachable (HTTP 200), otherwise False.

    This function is non-interactive and silent; callers handle messaging.
    """
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except Exception:
        return False


def check_mcp_streamable(url: str, timeout: int = 5) -> bool:
    init_payload = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "id": 1,
        "params": {}
    }
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json"
    }
    try:
        resp = requests.post(url, json=init_payload, headers=headers, timeout=timeout, stream=True)
        # Check HTTP status and content type
        ok = resp.status_code == 200 or resp.status_code == 202
        ctype = resp.headers.get("Content-Type", "")
        if ok and ("application/json" in ctype or "text/event-stream" in ctype):
            return True
    except Exception:
        return False
    return False


def test_comfyui_connection(url: str) -> bool:
    """Test ComfyUI connectivity using /system_stats endpoint."""
    try:
        response = requests.get(urljoin(url, "/system_stats"), timeout=3)
        return response.status_code == 200
    except Exception:
        return False


def test_ollama_connection(base_url: str) -> bool:
    """Test Ollama connectivity using /api/tags endpoint.

    Accepts either base_url with or without "/v1" suffix.
    """
    try:
        test_url = base_url.replace("/v1", "")
        response = requests.get(f"{test_url}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def get_openai_models(api_key: str, base_url: str) -> List[str]:
    """Fetch available OpenAI(-compatible) models; returns deduplicated list in original order.

    Returns all available models without filtering, letting users choose themselves.
    """
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(f"{base_url}/models", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            models = [model.get("id", "") for model in data.get("data", [])]
            # Remove duplicates while preserving order
            seen = set()
            deduplicated_models = []
            for model in models:
                if model and model not in seen:
                    seen.add(model)
                    deduplicated_models.append(model)
            return deduplicated_models
    except Exception:
        pass
    return []


def get_ollama_models(base_url: str) -> List[str]:
    """Fetch available Ollama models from /api/tags; returns list of names."""
    try:
        test_url = base_url.replace("/v1", "")
        response = requests.get(f"{test_url}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [model.get("name", "") for model in data.get("models", [])]
    except Exception:
        pass
    return []


