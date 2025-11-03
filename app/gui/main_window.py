from __future__ import annotations

from typing import Optional

import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import QInputDialog, QWidget

from app.bus import Bus
from app.engine_adapter import EngineAdapter
from app.gui.bottom_overlay import BottomOverlay
from app.gui.character_pane import CharacterPane
from app.gui.knowledge_pane import KnowledgePane
from app.gui.nav_overlay import NavOverlay
from app.gui.scene import CenterScene
from app.gui.sliding_pane import SlidingPane
from app.loaders import load_character, load_knowledge
from script_loader import load_script


class MainWindow(QWidget):
    def __init__(self, seed: Optional[int] = None):
        super().__init__()
        self.setMinimumSize(1280, 720)
        self.bus = Bus()
        self._logger = logging.getLogger(__name__)

        self.script = load_script()
        self.ui_strings = self.script.get("ui", {})
        main_ui = self.ui_strings.get("main_window", {})
        self.setWindowTitle(main_ui.get("title", "CRPG–VN Hybrid (Long Twilight)"))

        # Center scene (background + sprite)
        self.scene = CenterScene(self)
        self.bus.scene_changed.connect(self._update_scene)

        # UI overlays
        self.nav = NavOverlay(
            self.bus,
            ui_strings=self.ui_strings.get("nav_overlay"),
            parent=self,
        )

        # Panes
        char_data = load_character()
        know_data = load_knowledge()

        self.left = SlidingPane(
            "left",
            width_px=360,
            title=char_data.get("name", "You"),
            parent=self,
        )
        knowledge_title = main_ui.get("knowledge_title", "Knowledge")
        self.right = SlidingPane(
            "right",
            width_px=420,
            title=knowledge_title,
            parent=self,
        )

        self.char_pane = CharacterPane(
            parent=self.left,
            ui_strings=self.ui_strings.get("character_pane"),
        )
        self.char_pane.bind_bus(self.bus)
        self.left.content.addWidget(self.char_pane)

        self.know_pane = KnowledgePane(
            parent=self.right,
            ui_strings=self.ui_strings.get("knowledge_pane"),
        )
        self.know_pane.bind_bus(self.bus)
        self.right.content.addWidget(self.know_pane)

        # Bottom overlay
        self.overlay = BottomOverlay(self.bus, parent=self)

        # Seed panes
        self._emit_character(char_data)
        self.bus.inventory_updated.emit(char_data.get("inventory", []))
        self.bus.knowledge_updated.emit(know_data)

        # Hotkeys
        self._bind_hotkeys()

        # Signal plumbing
        self.bus.travel_chosen.connect(self._travel)
        self.bus.talk_to.connect(self._talk)

        # Deterministic seed controls
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        self._seed: Optional[int] = None
        self._deterministic_action = self._create_deterministic_action()

        # Engine setup
        self.engine: Optional[EngineAdapter] = None
        self._init_engine(seed)

    def _create_deterministic_action(self) -> QAction:
        determinism_ui = self.ui_strings.get("determinism", {})
        label = determinism_ui.get("action_label")
        if not label:
            label = self.ui_strings.get("main_window", {}).get(
                "deterministic_seed_action",
                "Deterministic Seed",
            )
        action = QAction(label, self)
        shortcut = determinism_ui.get("deterministic_seed_shortcut")
        if not shortcut:
            shortcut = self.ui_strings.get("main_window", {}).get(
                "deterministic_seed_shortcut",
                "Ctrl+D",
            )
        if shortcut:
            action.setShortcut(shortcut)
        action.triggered.connect(self._prompt_deterministic_seed)
        self.addAction(action)
        return action

    def _prompt_deterministic_seed(self) -> None:
        determinism_ui = self.ui_strings.get("determinism", {})
        title = determinism_ui.get("dialog_title", "Deterministic Seed")
        prompt = determinism_ui.get(
            "dialog_prompt", "Enter a seed for deterministic simulation:"
        )
        current = self._seed if self._seed is not None else 0
        seed, ok = QInputDialog.getInt(self, title, prompt, current)
        if ok:
            self._seed = seed
            self._init_engine(seed)
            toast = determinism_ui.get("toast", "")
            if toast:
                self.bus.toast.emit(toast.format(seed=seed))

    def _init_engine(self, seed: Optional[int]) -> None:
        self._seed = seed
        try:
            self.engine = EngineAdapter(self.bus, seed=seed)
            self.engine.advance_dialogue()
        except Exception as exc:  # pragma: no cover - UI safety net
            self._logger.exception("Failed to initialise engine")
            self.bus.toast.emit(str(exc))
            self.engine = None

    def _emit_character(self, c):
        snap = {
            "name": c.get("name", "You"),
            "level": c.get("level", 1),
            "hp": c.get("hp", 1),
            "mp": c.get("mp", 0),
            "stamina": c.get("stamina", 0),
            "attrs": c.get("attrs", {}),
            "skills": c.get("skills", {}),
            "conditions": c.get("conditions", []),
            "affinity": c.get("affinity", {}),
        }
        self.bus.stats_updated.emit(snap)

    def _bind_hotkeys(self):
        QShortcut(QKeySequence("Tab"), self, activated=self.toggle_left)
        QShortcut(QKeySequence("Shift+Tab"), self, activated=self.toggle_right)
        QShortcut(QKeySequence("Space"), self, activated=self.advance)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self._save)
        QShortcut(QKeySequence("Ctrl+L"), self, activated=self._load)
        QShortcut(QKeySequence("H"), self, activated=self.toggle_history)
        # numeric choices 1..9
        for n in range(1, 10):
            QShortcut(
                QKeySequence(str(n)),
                self,
                activated=lambda i=n: self.bus.option_chosen.emit(i),
            )

        self.bus.option_chosen.connect(self.choose)

    def _update_scene(self, payload: dict):
        self.scene.set_background(payload.get("bg"))
        self.scene.set_sprite(payload.get("sprite"))

    def resizeEvent(self, _):
        r = self.rect()
        # layout: scene fills, panes float, overlay at bottom
        self.scene.setGeometry(0, 0, r.width(), r.height())
        self.left.reposition(r)
        self.right.reposition(r)
        self.nav.setGeometry(0, 0, r.width(), 64)
        self.overlay.resize_to(r, 240)

    def toggle_left(self):
        self.left.toggle(self.rect())

    def toggle_right(self):
        self.right.toggle(self.rect())

    def advance(self):
        if self.engine:
            self._safe_call(self.engine.advance_dialogue)

    def choose(self, option_id: int):
        if self.engine:
            self._safe_call(self.engine.apply_choice, option_id)

    def _travel(self, exit_key: str):
        if self.engine:
            self._safe_call(self.engine.travel_to, exit_key)

    def toggle_history(self):
        self.overlay.toggle_history()

    def _talk(self, girl_name: str):
        if self.engine:
            self._safe_call(self.engine.focus, girl_name)

    def _save(self):
        if self.engine:
            self._safe_call(self.engine.save)

    def _load(self):
        if self.engine:
            self._safe_call(self.engine.load)

    def _safe_call(self, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:  # pragma: no cover - UI safety net
            self._logger.exception("Engine interaction failed")
            self.bus.toast.emit(str(exc))
            return None
