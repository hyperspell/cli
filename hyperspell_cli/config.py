from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

CONFIG_DIR = Path.home() / ".hyperspell"
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULT_BASE_URL = "https://api.hyperspell.com"


def load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(data: Dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.chmod(0o700)
    CONFIG_PATH.write_text(json.dumps(data, indent=2) + "\n")


def clear_config() -> None:
    if CONFIG_PATH.exists():
        CONFIG_PATH.unlink()


def resolve_api_key() -> str:
    from hyperspell_cli.lib.output import output_error

    key = os.environ.get("HYPERSPELL_API_KEY")
    if key:
        return key

    cfg = load_config()
    key = cfg.get("api_key")
    if key:
        return key

    output_error(
        "No API key found. Set HYPERSPELL_API_KEY or run: hyperspell auth login",
        code="no_api_key",
    )
    return ""  # unreachable


def resolve_base_url() -> str:
    url = os.environ.get("HYPERSPELL_BASE_URL")
    if url:
        return url

    cfg = load_config()
    url = cfg.get("base_url")
    if url:
        return url

    return DEFAULT_BASE_URL


def resolve_user_id(flag: Optional[str] = None) -> Optional[str]:
    """Resolve user ID for X-As-User header."""
    if flag:
        return flag

    user_id = os.environ.get("HYPERSPELL_USER_ID")
    if user_id:
        return user_id

    cfg = load_config()
    return cfg.get("user_id")


def get_sdk_client():
    """Return a Hyperspell SDK client."""
    from hyperspell import Hyperspell

    kwargs: Dict[str, Any] = {"api_key": resolve_api_key(), "base_url": resolve_base_url()}
    user_id = resolve_user_id()
    if user_id:
        kwargs["default_headers"] = {"X-As-User": user_id}
    return Hyperspell(**kwargs)


def get_http_client():
    """Return an httpx client with API key auth."""
    import httpx

    headers: Dict[str, str] = {"X-API-Key": resolve_api_key()}
    user_id = resolve_user_id()
    if user_id:
        headers["X-As-User"] = user_id

    return httpx.Client(base_url=resolve_base_url(), headers=headers, timeout=30)


def serialize(obj: Any) -> Any:
    """Convert an SDK model (or list of models) to a JSON-serializable dict."""
    if isinstance(obj, list):
        return [serialize(item) for item in obj]
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return obj
