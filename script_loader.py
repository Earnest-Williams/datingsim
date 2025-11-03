import os
from typing import Any, Dict, Optional

import yaml

_SCRIPT_CACHE: Optional[Dict[str, Any]] = None


def load_script() -> Dict[str, Any]:
    """Load and cache the narrative script data."""
    global _SCRIPT_CACHE
    if _SCRIPT_CACHE is None:
        script_path = os.path.join(os.path.dirname(__file__), "script.yaml")
        with open(script_path, "r", encoding="utf-8") as script_file:
            _SCRIPT_CACHE = yaml.safe_load(script_file) or {}
    return _SCRIPT_CACHE
