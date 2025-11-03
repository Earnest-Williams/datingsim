from typing import Dict, Any, List, Tuple, Optional

from app.bus import Bus
from script_loader import load_script
from elements import Engine, Character, Girl
from location_definitions import location_list
from girl_definitions import girl_list
from locationobj import activate_location


class _NullInput:
    """Minimal stand-in for the text engine's Input object."""

    def __init__(self):
        self.verb: List[str] = []
        self.direction: List[str] = []
        self.noun: List[str] = []
        self.character: List[str] = []
        self.inactive_verb: List[str] = []
        self.vocab = {
            "verb": self.verb,
            "direction": self.direction,
            "noun": self.noun,
            "character": self.character,
            "inactive_verb": self.inactive_verb,
        }

class EngineAdapter:
    """
    Bridges legacy engine state to GUI overlay:
      - Initializes Engine/Character and locations/girls.
      - Maintains a focused character.
      - Reads script.yaml dialogue trees and produces VN-style payloads.
      - Applies choice effects (opinion changes, acquaintance, date setup).
    """

    def __init__(self, bus: Bus):
        self.bus = bus
        self.script = load_script()               # dialogue, dialogue_trees, girls
        self.dialogue_text = self.script["dialogue"]
        self.dialogue_trees = self.script["dialogue_trees"]

        # Legacy engine bootstrap
        self.e = Engine()
        self.mc = Character()
        self.e.build_locations(location_list)
        self.e.build_girls(girl_list)

        # Start day at a useful spot and seed a starter NPC
        self.mc.get_name("Protagonist")
        activate_location(self.e, "residential district", _NullInput(), self.mc)  # sets current_location, verbs, etc.
        self.e.start_day()

        # Focus a reasonable default (tammy) so dialogue works in GUI
        self.focus("tammy")

        # Dialogue traversal state
        self._levels: List[Tuple[int, Dict[str, Any]]] = self._ordered_levels()
        self._level_index: int = 0
        self._pending_date: bool = False
        self._awaiting_confirmation: bool = False

    # ---------- high-level API consumed by GUI ----------

    def next_dialogue_payload(self) -> Dict[str, Any]:
        """
        Return {speaker, text, options:[{id,label}...]}.
        Chooses which option set to display based on acquaintance and opinion,
        mirroring getdialogue.py logic but without blocking input().
        """
        girl = self._focused()
        if girl is None:
            return {"speaker": "", "text": "No one is here.", "options": [{"id": 1, "label": "Continue"}]}

        # greet/encounter text once per node (simple)
        speaker = girl.name.title()
        text = self.dialogue_text["greeting"]

        # Which level to use
        level_num, level = self._current_level()

        # Known?
        known = girl.name in self.mc.known_girls
        opinion = girl.opinion

        # Options mirror console:
        if not known:
            opts = [
                {"id": 1, "label": level["statement"]["compliment"]},
                {"id": 2, "label": f'{level["statement"]["introduction"]} {self.mc.name}'},
                {"id": 3, "label": level["statement"]["question"]},
            ]
        else:
            base = [
                {"id": 1, "label": level["statement"]["compliment"]},
                {"id": 2, "label": self._random_observation()},
                {"id": 3, "label": level["statement"]["question"]},
            ]
            if opinion >= 3:
                base.append({"id": 4, "label": self.dialogue_text["date_offer"]})
            opts = base

        # Informational prefix (level/opinion) in the text block, like console
        header = f"{self.dialogue_text['level_label']} {level_num}\n{self.dialogue_text['opinion_label']} {opinion}"
        return {
            "speaker": speaker,
            "text": f"{header}\n\n{text}",
            "options": opts,
        }

    def apply_choice(self, option_id: int):
        """Apply the effects for the selected option and advance state."""
        girl = self._focused()
        if girl is None:
            return

        if self._awaiting_confirmation:
            self._awaiting_confirmation = False
            self._advance_level()
            return

        _, level = self._current_level()

        def bump(key: str):
            delta = level["reply"][key][1]
            girl.opinion += delta

        # Not known yet
        if girl.name not in self.mc.known_girls:
            if option_id == 1:
                bump("compliment")
            elif option_id == 2:
                self.mc.make_acquaintance(girl)
                bump("introduction")
            elif option_id == 3:
                bump("question")

        else:
            # Known but low opinion
            if girl.opinion < 3:
                if option_id == 1:
                    bump("compliment")
                elif option_id == 2:
                    bump("observation")
                elif option_id == 3:
                    bump("question")
            else:
                # High opinion; may include date
                if option_id == 1:
                    bump("compliment")
                elif option_id == 2:
                    bump("observation")
                elif option_id == 3:
                    bump("question")
                elif option_id == 4:
                    # Present date destinations next time; store transient intent
                    self._pending_date = True

        # If a date was requested, inject a date-selection node once, using script["dialogue"]["date_choices"]
        if getattr(self, "_pending_date", False):
            self._pending_date = False
            self._show_date_choices()
            return

        self._advance_level()

    # ---------- internals ----------

    def focus(self, girl_name: str):
        """Set the current focus character by name (lowercase keys)."""
        try:
            self.mc.focus(self.e.girls[girl_name])
        except KeyError:
            # Fallback: focus the first available
            if self.e.girls:
                first = next(iter(self.e.girls.keys()))
                self.mc.focus(self.e.girls[first])

        # Reset traversal on new focus
        self._levels = self._ordered_levels()
        self._level_index = 0

    def _focused(self) -> Optional[Girl]:
        return self.mc.focus_character

    def _ordered_levels(self) -> List[Tuple[int, Dict[str, Any]]]:
        """Sort levels like console (keys '0','1',...)."""
        tree_name = "default"
        if self._focused() is not None:
            # girl_list was already expanded with a dialogue_tree (dict)
            # but we prefer the canonical script tree for consistency
            tree_name = "default"
        tree = self.dialogue_trees[tree_name]
        items = []
        for k, v in tree.items():
            try:
                items.append((int(k), v))
            except ValueError:
                items.append((k, v))
        items.sort(key=lambda kv: kv[0])
        return items

    def _current_level(self) -> Tuple[int, Dict[str, Any]]:
        return self._levels[self._level_index]

    def _random_observation(self) -> str:
        loc = self.e.current_location
        return loc.observations[0] if loc and loc.observations else "…"

    def _show_date_choices(self):
        """Emit a one-off payload to pick a date destination; apply immediately on click."""
        choices = self.dialogue_text["date_choices"]
        payload = {
            "speaker": self._focused().name.title() if self._focused() else "",
            "text": f"{self.dialogue_text['date_invite']}",
            "options": [{"id": i + 1, "label": c["text"]} for i, c in enumerate(choices)],
        }
        # Temporarily hijack option handling to map 1..N to chosen location
        def _handle(choice_id: int):
            idx = max(1, min(choice_id, len(choices))) - 1
            loc_key = choices[idx]["location"]
            self._make_date(loc_key)
            # Confirmation text next advance
            self._last_confirmation = self.dialogue_text["date_confirmation"]

        # Install a one-shot handler by monkeypatching, then restore after click
        original_apply = self.apply_choice
        def one_shot(option_id: int):
            try:
                _handle(option_id)
            finally:
                # restore and auto-advance to confirmation
                self.apply_choice = original_apply
                self._emit_confirmation_then_day()
        self.apply_choice = one_shot  # type: ignore

        # Tell the overlay to show the date options now
        self.bus.dialogue_ready.emit(payload)

    def _make_date(self, loc_key: str):
        girl = self._focused()
        if girl is None:
            return
        # Mark date at target location
        self.e.make_date(self.e.locations[loc_key], girl)

    def _emit_confirmation_then_day(self):
        # show confirmation text once
        txt = getattr(self, "_last_confirmation", "Okay.")
        payload = {
            "speaker": self._focused().name.title() if self._focused() else "",
            "text": txt,
            "options": [{"id": 1, "label": "Continue"}],
        }
        self.bus.dialogue_ready.emit(payload)
        self._awaiting_confirmation = True
        # after the user clicks "Continue", resume normal flow

    def _advance_level(self):
        self._level_index = min(self._level_index + 1, len(self._levels) - 1)
        self.e.start_day()
