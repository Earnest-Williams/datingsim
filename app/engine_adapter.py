from typing import Dict, Any
from app.bus import Bus

class EngineAdapter:
    """Thin adapter to bridge engine state to UI. Extend as RPG/VN systems grow."""
    def __init__(self, bus: Bus):
        self.bus = bus
        self._node_id = None

    def next_dialogue_payload(self) -> Dict[str, Any]:
        # Minimal placeholder payload so the overlay is demonstrably working.
        return {
            "speaker": "Alice",
            "text": "Long twilight or not, we keep moving. Ready?",
            "options": [
                {"id": 1, "label": "Yes"},
                {"id": 2, "label": "Not yet"},
            ],
        }

    def apply_choice(self, option_id: int):
        # No-op for now. Wire into real dialogue/engine later.
        pass
