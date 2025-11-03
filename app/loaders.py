import os, yaml
from typing import Any, Dict

CHAR_PATH = os.path.join("game", "character.yaml")
KNOW_PATH = os.path.join("game", "knowledge.yaml")
ASSET_PATH = os.path.join("game", "assets.yaml")

def _safe_load_yaml(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def load_character() -> Dict[str, Any]:
    data = _safe_load_yaml(CHAR_PATH)
    # Normalize shapes
    data.setdefault("attrs", {})
    data.setdefault("skills", {})
    data.setdefault("conditions", [])
    data.setdefault("affinity", {})
    data.setdefault("inventory", [])
    data.setdefault("currency", {"scrip": 0})
    data.setdefault("level", 1)
    data.setdefault("hp", 1)
    data.setdefault("mp", 0)
    data.setdefault("stamina", 0)
    data.setdefault("name", "Protagonist")
    return data

def load_knowledge() -> Dict[str, Any]:
    data = _safe_load_yaml(KNOW_PATH)
    for k in ("notes", "factions", "sites", "tech"):
        data.setdefault(k, [])
    return data


def load_assets() -> Dict[str, Any]:
    data = _safe_load_yaml(ASSET_PATH)
    data.setdefault("locales", {})
    data.setdefault("sprites", {})
    defaults = data.setdefault("defaults", {})
    defaults.setdefault("background", "assets/locales/classroom_generic.png")
    return data
