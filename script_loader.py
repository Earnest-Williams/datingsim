from __future__ import annotations
import os, json, yaml
from typing import Any, Dict

SCRIPT_PATHS = [
    os.path.join("game", "script.yaml"),
    os.path.join("game", "script.yml"),
    os.path.join("game", "script.json"),
]

_DEFAULT_SCRIPT: Dict[str, Any] = {
    "ui": {
        "general": {"continue_label": "Continue", "ellipsis": "…"},
        "dialogue": {"empty_scene": {"speaker": "", "text": "No one is here."}},
        "nav_overlay": {"location_placeholder": "—", "talk_label": " Talk: ", "talk_button": "Talk"},
        "main_window": {
            "title": "CRPG–VN Hybrid (Long Twilight)",
            "deterministic_seed_action": "Deterministic Seed",
            "deterministic_seed_shortcut": "Ctrl+D",
            "knowledge_title": "Knowledge",
        },
        "character_pane": {},
        "knowledge_pane": {
            "notes_tab": "Notes",
            "factions_tab": "Factions & Enclaves",
            "sites_tab": "Sites & Rumours",
            "tech_tab": "Tech & Lore",
            "status_placeholder": "",
        },
        "determinism": {
            "action_label": "Deterministic Seed",
            "dialog_title": "Deterministic Seed",
            "dialog_prompt": "Enter a seed for deterministic simulation:",
            "toast": "Deterministic seed set to {seed}.",
        },
    },
    "dialogue": {
        "greeting": "Hey.",
        "choice_prompt": "Choose an approach:",
        "level_label": "Level",
        "opinion_label": "Opinion",
        "date_offer": "Do you want to go somewhere together?",
        "date_invite": "Where should we go?",
        "date_confirmation": "Okay, let’s do it.",
        "date_choices": [
            {"text": "Walk by the river", "location": "river"},
            {"text": "Grab a bite at the restaurant", "location": "restaurant"},
            {"text": "Hit the club", "location": "club"},
        ],
        "encounter_message": "You run into {name}.",
    },
    "dialogue_trees": {
        "default": {
            "0": {
                "statement": {
                    "compliment": "You look sharp today.",
                    "introduction": "Hi, I’m",
                    "question": "Rough day?",
                },
                "reply": {
                    "compliment": ["Thanks.", 1],
                    "introduction": ["Nice to meet you.", 1],
                    "question": ["Could be worse.", 0],
                    "observation": ["Mm-hmm.", 0],
                },
            },
            "1": {
                "statement": {
                    "compliment": "That colour suits you.",
                    "introduction": "I’m",
                    "question": "Coffee later?",
                },
                "reply": {
                    "compliment": ["You think?", 1],
                    "introduction": ["We’ve met now.", 1],
                    "question": ["Maybe.", 1],
                    "observation": ["Right.", 0],
                },
            },
        }
    },
}


def _load_yaml_or_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        if path.endswith((".yaml", ".yml")):
            return yaml.safe_load(f) or {}
        return json.load(f)


def load_script() -> Dict[str, Any]:
    for p in SCRIPT_PATHS:
        if os.path.exists(p):
            data = _load_yaml_or_json(p)
            data.setdefault("ui", {})
            data.setdefault("dialogue", {})
            data.setdefault("dialogue_trees", {})
            for k, v in _DEFAULT_SCRIPT.items():
                if k not in data:
                    data[k] = v
            return data
    return _DEFAULT_SCRIPT.copy()
