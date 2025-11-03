from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import contextlib
import io

from app.bus import Bus
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

    def _quiet(self):
        return contextlib.redirect_stdout(io.StringIO())

    def __init__(self, bus: Bus, *, seed: Optional[int] = None):
        self.bus = bus
        if seed is not None:
            set_location_random_seed(seed)
            set_dialogue_random_seed(seed)
            set_experience_random_seed(seed)

        self.script = load_script()
        self.dialogue_text = self.script["dialogue"]
        self.dialogue_trees = self.script["dialogue_trees"]

        self.e = Engine()
        self.mc = Character()
        self.e.build_locations(location_list)
        self.e.build_girls(girl_list)

        self.mc.get_name("Protagonist")
        with self._quiet():
            activate_location(self.e, "residential district", Input(), self.mc)
            self.e.start_day()

        # Background/sprite asset maps.
        self._bg_by_loc: Dict[str, str] = {
            "residential district": "assets/locales/classroom_generic.png",
            "club": "assets/locales/classroom_generic.png",
            "restaurant": "assets/locales/classroom_generic.png",
            "city": "assets/locales/classroom_generic.png",
            "school": "assets/locales/Library_Nook.png",
        }
        self._sprite_for: Dict[str, str] = {
            "neutral": "assets/girls/Alice/Alice_Neutral_Transparent.png",
            "happy": "assets/girls/Alice/Alice_Happy_Transparent.png",
        }

        # Focus a default character so GUI dialogue works.
        self.focus("tammy")

        # Dialogue traversal state
        self._levels: List[Tuple[int, Dict[str, Any]]] = self._ordered_levels()
        self._level_index: int = 0
        self._pending_date = False
        self._emit_scene()

    # -------- GUI API --------
    def next_dialogue_payload(self) -> Dict[str, Any]:
        girl = self._focused()
        if girl is None:
            return {
                "speaker": "",
                "text": "No one is here.",
                "options": [{"id": 1, "label": "Continue"}],
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
        with self._quiet():
            self.e.start_day()
        self._emit_scene()

    def travel_to(self, exit_key: str) -> None:
        if not self.e.current_location:
            return
        _inp = Input()
        with self._quiet():
            activate_location(self.e, exit_key, _inp, self.mc)
            self.e.start_day()
        self._emit_scene()

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
        return loc.observations[0] if loc and loc.observations else "…"

    def _snapshot_nav(self) -> Dict[str, Any]:
        loc = self.e.current_location
        exits: List[Dict[str, str]] = []
        if loc:
            for label in loc.destinations.keys():
                exits.append({"id": label, "label": label})
        chars = list(loc.characters) if loc else []
        return {
            "location": loc.name if loc else "",
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

    def _emit_stats(self) -> None:
        self.bus.stats_updated.emit(
            {
                "name": self.mc.name or "You",
                "level": 1,
                "hp": self.mc.__dict__.get("hp", 1),
                "mp": self.mc.__dict__.get("mp", 0),
                "stamina": self.mc.__dict__.get("stamina", 0),
                "attrs": {},
                "skills": {},
                "conditions": [],
                "affinity": {},
            }
        )

    def _emit_scene(self) -> None:
        loc_name = self.e.current_location.name if self.e.current_location else ""
        bg = self._bg_by_loc.get(loc_name, "assets/locales/classroom_generic.png")
        sprite: Optional[str] = None
        girl = self._focused()
        if girl:
            sprite = (
                self._sprite_for["happy"]
                if girl.opinion >= 2
                else self._sprite_for["neutral"]
            )
        self.bus.scene_changed.emit({"bg": bg, "sprite": sprite})
        self._emit_nav()
        self._emit_state()

    def _show_date_choices(self) -> None:
        choices = self.dialogue_text["date_choices"]
        payload = {
            "speaker": self._focused().name.title() if self._focused() else "",
            "text": f"{self.dialogue_text['date_invite']}",
            "options": [{"id": i + 1, "label": choice["text"]} for i, choice in enumerate(choices)],
        }

        def _handle(choice_id: int) -> None:
            idx = max(1, min(choice_id, len(choices))) - 1
            loc_key = choices[idx]["location"]
            with self._quiet():
                self.e.make_date(self.e.locations[loc_key], self._focused())
            self.bus.dialogue_ready.emit(
                {
                    "speaker": self._focused().name.title() if self._focused() else "",
                    "text": self.dialogue_text["date_confirmation"],
                    "options": [{"id": 1, "label": "Continue"}],
                }
            )
            self._emit_scene()

        original_apply = self.apply_choice

        def once(option: int) -> None:
            try:
                _handle(option)
            finally:
                self.apply_choice = original_apply

        self.apply_choice = once  # type: ignore[assignment]
        self.bus.dialogue_ready.emit(payload)
