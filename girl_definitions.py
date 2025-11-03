from copy import deepcopy
from script_loader import load_script

DEFAULT_DIALOGUE_TREE = "default"

_script = load_script()
_dialogue_trees = _script.get("dialogue_trees", {})
_girl_dialogues = _script.get("girls", {})


def _dialogue_tree_for(girl_name):
    tree_name = DEFAULT_DIALOGUE_TREE

    girl_config = _girl_dialogues.get(girl_name)
    if girl_config is not None:
        tree_name = girl_config.get("dialogue_tree", DEFAULT_DIALOGUE_TREE)
    elif DEFAULT_DIALOGUE_TREE not in _dialogue_trees:
        raise KeyError(
            f"No dialogue tree configured for girl '{girl_name}', and no default tree defined."
        )

    try:
        return deepcopy(_dialogue_trees[tree_name])
    except KeyError as exc:
        raise KeyError(
            f"Dialogue tree '{tree_name}' referenced by girl '{girl_name}' is not defined."
        ) from exc


_base_girl_definitions = {
    "tammy": {
        "love": 15,
        "prude": "easy",
        "affinity": "club",
        "meet_at": "bar",
        "see_at": ["bar", "night life district", "historic district"],
    },
    "liz": {
        "love": 10,
        "prude": "easy",
        "affinity": "restaurant",
        "meet_at": "work",
        "see_at": ["work", "city", "shopping district"],
    },
    "jasmine": {
        "love": 5,
        "prude": "hard",
        "affinity": "club",
        "meet_at": "school",
        "see_at": ["school", "walking path", "historic district"],
    },
    "claire": {
        "love": 10,
        "prude": "med",
        "affinity": "club",
        "meet_at": "shopping district",
        "see_at": ["shopping district", "store", "historic district"],
    },
    "rebecca": {
        "love": 5,
        "prude": "med",
        "affinity": "club",
        "meet_at": "store",
        "see_at": ["shopping district", "store", "city"],
    },
    "brittany": {
        "love": 5,
        "prude": "easy",
        "affinity": "club",
        "meet_at": "night life district",
        "see_at": ["night life district", "bar", "city"],
    },
    "kerry": {
        "love": 15,
        "prude": "hard",
        "affinity": "club",
        "meet_at": "hiking trails",
        "see_at": ["walking path", "hiking trails", "historic district"],
    },
    "ricky": {
        "love": 15,
        "prude": "med",
        "affinity": "club",
        "meet_at": "theatre district",
        "see_at": ["theatre district", "school", "city"],
    },
    "donika": {
        "love": 10,
        "prude": "hard",
        "affinity": "club",
        "meet_at": "gym",
        "see_at": ["gym", "work", "historic district"],
    },
}

girl_list = {}
for name, attributes in _base_girl_definitions.items():
    entry = dict(attributes)
    entry["dialogue_tree"] = _dialogue_tree_for(name)
    girl_list[name] = entry
