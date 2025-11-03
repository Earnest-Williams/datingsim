from __future__ import annotations

import os
from collections import deque
from copy import deepcopy
from typing import Any, Deque, Dict, List, Optional, Tuple

import yaml

from app.bus import Bus
from app.loaders import load_character, load_assets
from elements import Character, Engine, Girl
from girl_definitions import girl_list
from location_definitions import location_list
from expobject import set_random_seed as set_experience_random_seed
from getdialogue import set_random_seed as set_dialogue_random_seed
from locationobj import activate_location, set_random_seed as set_location_random_seed
from script_loader import load_script
from getinputobject import Input

class EngineAdapter:
    """Bridge the legacy engine with the Qt GUI overlay."""

    def __init__(self, bus: Bus, *, seed: Optional[int] = None):
        self.bus = bus
        self._toast_history: Deque[str] = deque(maxlen=20)
        self.bus.toast_history.emit(list(self._toast_history))
        if seed is not None:
            set_location_random_seed(seed)
            set_dialogue_random_seed(seed)
            set_experience_random_seed(seed)

        self.script = load_script()
        self.dialogue_text = self.script["dialogue"]
        self.dialogue_trees = self.script["dialogue_trees"]
        self.ui_text = self.script.get("ui", {})
        self._general_ui = self.ui_text.get("general", {})
        self._dialogue_ui = self.ui_text.get("dialogue", {})
        self._nav_ui = self.ui_text.get("nav_overlay", {})

        self.e = Engine()
        self.mc = Character()
        self._base_stats = load_character()
        self.e.build_locations(location_list)
        self.e.build_girls(girl_list)

        self.mc.get_name("Protagonist")
        arrival = activate_location(self.e, "residential district", Input(), self.mc)
        day_message: Optional[str] = None
        if str(self.e.state) != "date_state":
            day_message = self.e.start_day()
        self._toast(*arrival, day_message)

        assets = load_assets()
        self._bg_by_loc = dict(assets.get("locales", {}))
        self._sprite_for = dict(assets.get("sprites", {}))
        defaults = assets.get("defaults", {})
        self._default_bg = defaults.get(
            "background", "assets/locales/classroom_generic.png"
        )
        self._neutral_sprite = self._sprite_for.get("neutral")
        self._happy_sprite = self._sprite_for.get("happy")

        # Focus a default character so GUI dialogue works.
        self.focus("tammy")

        # Dialogue traversal state
        self._levels: List[Tuple[int, Dict[str, Any]]] = self._ordered_levels()
        self._level_index: int = 0
        self._pending_date = False
        self._emit_scene()

    def _toast(self, *lines: Optional[str]) -> None:
        message = "\n".join(line for line in lines if line)
        if message.strip():
            self._toast_history.append(message)
            self.bus.toast_history.emit(list(self._toast_history))
            self.bus.toast.emit(message)

    # -------- GUI API --------
    def next_dialogue_payload(self) -> Dict[str, Any]:
        girl = self._focused()
        if girl is None:
            empty_state = self._dialogue_ui.get("empty_scene", {})
            continue_label = self._general_ui.get("continue_label", "Continue")
            return {
                "speaker": empty_state.get("speaker", ""),
                "text": empty_state.get("text", "No one is here."),
                "options": [{"id": 1, "label": continue_label}],
            }

        speaker = girl.name.title()
        level_num, level = self._current_level()
        known = girl.name in self.mc.known_girls
        opinion = girl.opinion

        header = (
            f"{self.dialogue_text['level_label']} {level_num}\n"
            f"{self.dialogue_text['opinion_label']} {opinion}"
        )
        text = f"{header}\n\n{self.dialogue_text['greeting']}"

        if not known:
            opts = [
                {"id": 1, "label": level["statement"]["compliment"]},
                {
                    "id": 2,
                    "label": f"{level['statement']['introduction']} {self.mc.name}",
                },
                {"id": 3, "label": level["statement"]["question"]},
            ]
        else:
            opts = [
                {"id": 1, "label": level["statement"]["compliment"]},
                {"id": 2, "label": self._random_observation()},
                {"id": 3, "label": level["statement"]["question"]},
            ]
            if opinion >= 3:
                opts.append({"id": 4, "label": self.dialogue_text["date_offer"]})

        return {"speaker": speaker, "text": text, "options": opts}

    def advance_dialogue(self) -> Dict[str, Any]:
        payload = self.next_dialogue_payload()
        self.bus.dialogue_ready.emit(payload)
        return payload

    def apply_choice(self, option_id: int) -> None:
        girl = self._focused()
        if girl is None:
            self._emit_stats()
            return
        _, level = self._current_level()

        def bump(key: str) -> None:
            girl.opinion += level["reply"][key][1]

        if girl.name not in self.mc.known_girls:
            if option_id == 1:
                bump("compliment")
            elif option_id == 2:
                self.mc.make_acquaintance(girl)
                bump("introduction")
            elif option_id == 3:
                bump("question")
        else:
            if girl.opinion < 3:
                if option_id == 1:
                    bump("compliment")
                elif option_id == 2:
                    bump("observation")
                elif option_id == 3:
                    bump("question")
            else:
                if option_id == 1:
                    bump("compliment")
                elif option_id == 2:
                    bump("observation")
                elif option_id == 3:
                    bump("question")
                elif option_id == 4:
                    self._pending_date = True

        self._emit_stats()

        if self._pending_date:
            self._pending_date = False
            self._show_date_choices()
            return

        self._level_index = min(self._level_index + 1, len(self._levels) - 1)
        day_message = self.e.start_day()
        self._toast(day_message)
        self._emit_scene()
        self.advance_dialogue()

    def travel_to(self, exit_key: str) -> None:
        if not self.e.current_location:
            return
        _inp = Input()
        messages = activate_location(self.e, exit_key, _inp, self.mc)
        day_message: Optional[str] = None
        if str(self.e.state) != "date_state":
            day_message = self.e.start_day()
        self._toast(*messages, day_message)
        self._emit_scene()
        self.advance_dialogue()

    def save(self, path: str = "save.yaml") -> None:
        focused = self._focused()
        data = {
            "focused": focused.name if focused else None,
            "known_girls": list(self.mc.known_girls),
            "opinions": {girl.name: girl.opinion for girl in self.e.girls.values()},
            "location": self.e.current_location.name if self.e.current_location else None,
        }
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f)

    def load(self, path: str = "save.yaml") -> None:
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        known = data.get("known_girls", [])
        if isinstance(known, list):
            self.mc.known_girls = [str(name) for name in known]

        for name, val in (data.get("opinions") or {}).items():
            if name in self.e.girls:
                try:
                    self.e.girls[name].opinion = int(val)
                except (TypeError, ValueError):
                    continue

        if (foc := data.get("focused")):
            self.focus(foc)

        if (loc := data.get("location")):
            self.travel_to(loc)

    # -------- internals --------
    def focus(self, girl_name: str) -> None:
        try:
            self.mc.focus(self.e.girls[girl_name])
        except KeyError:
            if self.e.girls:
                fallback = next(iter(self.e.girls.values()))
                self.mc.focus(fallback)
        self._levels = self._ordered_levels()
        self._level_index = 0
        self._emit_stats()
        self._emit_scene()
        self.advance_dialogue()

    def _focused(self) -> Optional[Girl]:
        return self.mc.focus_character

    def _ordered_levels(self) -> List[Tuple[int, Dict[str, Any]]]:
        tree = self.dialogue_trees["default"]
        items: List[Tuple[int, Dict[str, Any]]] = []
        for key, value in tree.items():
            try:
                items.append((int(key), value))
            except ValueError:
                items.append((key, value))  # type: ignore[list-item]
        items.sort(key=lambda kv: kv[0])
        return items

    def _current_level(self) -> Tuple[int, Dict[str, Any]]:
        return self._levels[self._level_index]

    def _random_observation(self) -> str:
        loc = self.e.current_location
        if loc and loc.observations:
            return loc.observations[0]
        return self._general_ui.get("ellipsis", "…")

    def _snapshot_nav(self) -> Dict[str, Any]:
        loc = self.e.current_location
        exits: List[Dict[str, str]] = []
        if loc:
            for label in loc.destinations.keys():
                exits.append({"id": label, "label": label})
        chars = list(loc.characters) if loc else []
        return {
            "location": loc.name if loc else self._nav_ui.get("location_placeholder", ""),
            "exits": exits,
            "characters": chars,
        }

    def _emit_nav(self) -> None:
        self.bus.nav_ready.emit(self._snapshot_nav())

    def _emit_state(self) -> None:
        state = str(self.e.state)
        if state.endswith("_state"):
            state = state[: -len("_state")]
        self.bus.state_changed.emit(state)
        if state == "dialogue":
            self.advance_dialogue()

    def _emit_stats(self) -> None:
        stats = deepcopy(self._base_stats)
        stats["name"] = self.mc.name or stats.get("name", "You")
        stats["level"] = self.mc.__dict__.get("level", stats.get("level", 1))
        stats["hp"] = self.mc.__dict__.get("hp", stats.get("hp", 1))
        stats["mp"] = self.mc.__dict__.get("mp", stats.get("mp", 0))
        stats["stamina"] = self.mc.__dict__.get("stamina", stats.get("stamina", 0))

        affinity = stats.get("affinity", {})
        for girl_name, girl in self.e.girls.items():
            affinity[girl_name] = girl.opinion
        stats["affinity"] = affinity

        self.bus.stats_updated.emit(stats)

    def _emit_scene(self) -> None:
        loc_name = self.e.current_location.name if self.e.current_location else ""
        bg = self._bg_by_loc.get(loc_name, self._default_bg)
        sprite: Optional[str] = None
        girl = self._focused()
        if girl:
            if girl.opinion >= 2 and self._happy_sprite:
                sprite = self._happy_sprite
            elif self._neutral_sprite:
                sprite = self._neutral_sprite
        self.bus.scene_changed.emit({"bg": bg, "sprite": sprite})
        self._emit_nav()
        self._emit_state()

    def _show_date_choices(self) -> None:
        choices = self.dialogue_text["date_choices"]
        continue_label = self._general_ui.get("continue_label", "Continue")
        payload = {
            "speaker": self._focused().name.title() if self._focused() else "",
            "text": f"{self.dialogue_text['date_invite']}",
            "options": [{"id": i + 1, "label": choice["text"]} for i, choice in enumerate(choices)],
        }

        original_apply = self.apply_choice

        def _after_confirmation(_: int) -> None:
            try:
                self._level_index = min(self._level_index + 1, len(self._levels) - 1)
                day_message = self.e.start_day()
            finally:
                self.apply_choice = original_apply
            self._toast(day_message)
            self._emit_scene()
            self.advance_dialogue()

        def _handle(option: int) -> None:
            idx = max(1, min(option, len(choices))) - 1
            loc_key = choices[idx]["location"]
            self.e.make_date(self.e.locations[loc_key], self._focused())
            self.apply_choice = _after_confirmation  # type: ignore[assignment]
            self.bus.dialogue_ready.emit(
                {
                    "speaker": self._focused().name.title() if self._focused() else "",
                    "text": self.dialogue_text["date_confirmation"],
                    "options": [{"id": 1, "label": continue_label}],
                }
            )

        def _await_date(option: int) -> None:
            _handle(option)

        self.apply_choice = _await_date  # type: ignore[assignment]
        self.bus.dialogue_ready.emit(payload)
