from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtCore import Qt
from app.bus import Bus
from app.engine_adapter import EngineAdapter
from app.gui.sliding_pane import SlidingPane
from app.gui.bottom_overlay import BottomOverlay
from app.gui.character_pane import CharacterPane
from app.gui.knowledge_pane import KnowledgePane
from app.loaders import load_character, load_knowledge

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CRPG–VN Hybrid (Long Twilight)")
        self.setMinimumSize(1280, 720)
        self.bus = Bus()
        self.engine = EngineAdapter(self.bus)

        # Center scene placeholder
        self.scene = QLabel("Scene", self)
        self.scene.setAlignment(Qt.AlignCenter)
        self.scene.setStyleSheet("background:#0e1114; color:#d6a86b; font-size:20px;")

        # Panes
        char_data = load_character()
        know_data = load_knowledge()

        self.left = SlidingPane("left", width_px=360, title=char_data.get("name","You"), parent=self)
        self.right = SlidingPane("right", width_px=420, title="Knowledge", parent=self)

        self.char_pane = CharacterPane(parent=self.left)
        self.char_pane.bind_bus(self.bus)
        self.left.content.addWidget(self.char_pane)

        self.know_pane = KnowledgePane(parent=self.right)
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

        # First dialogue payload to demonstrate overlay
        self.advance()

    def _emit_character(self, c):
        snap = {
            "name": c.get("name","You"),
            "level": c.get("level",1),
            "hp": c.get("hp",1),
            "mp": c.get("mp",0),
            "stamina": c.get("stamina",0),
            "attrs": c.get("attrs",{}),
            "skills": c.get("skills",{}),
            "conditions": c.get("conditions",[]),
            "affinity": c.get("affinity",{}),
        }
        self.bus.stats_updated.emit(snap)

    def _bind_hotkeys(self):
        from PySide6.QtGui import QShortcut, QKeySequence
        QShortcut(QKeySequence("Tab"), self, activated=self.toggle_left)
        QShortcut(QKeySequence("Shift+Tab"), self, activated=self.toggle_right)
        QShortcut(QKeySequence("Space"), self, activated=self.advance)
        # numeric choices 1..9
        for n in range(1,10):
            QShortcut(QKeySequence(str(n)), self,
                      activated=lambda i=n: self.bus.option_chosen.emit(i))

        self.bus.option_chosen.connect(self.choose)

    def resizeEvent(self, _):
        r = self.rect()
        # layout: scene fills, panes float, overlay at bottom
        self.scene.setGeometry(0, 0, r.width(), r.height())
        self.left.reposition(r); self.right.reposition(r); self.overlay.resize_to(r, 240)

    def toggle_left(self):  self.left.toggle(self.rect())
    def toggle_right(self): self.right.toggle(self.rect())

    def advance(self):
        payload = self.engine.next_dialogue_payload()
        self.bus.dialogue_ready.emit(payload)

    def choose(self, option_id: int):
        self.engine.apply_choice(option_id)
        self.advance()
