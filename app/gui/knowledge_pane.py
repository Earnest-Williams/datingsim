from typing import Any, Dict, Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QTabWidget,
)

class KnowledgePane(QWidget):
    def __init__(self, *args, ui_strings: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(*args, **kwargs)
        ui = ui_strings or {}
        self._joiner = ui.get("entry_joiner", " — ")
        root = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.notes = QListWidget()
        self.factions = QListWidget()
        self.sites = QListWidget()
        self.tech = QListWidget()
        self.tabs.addTab(self.notes, ui.get("notes_tab", "Notes"))
        self.tabs.addTab(self.factions, ui.get("factions_tab", "Factions & Enclaves"))
        self.tabs.addTab(self.sites, ui.get("sites_tab", "Sites & Rumours"))
        self.tabs.addTab(self.tech, ui.get("tech_tab", "Tech & Lore"))
        root.addWidget(self.tabs)

    def bind_bus(self, bus):
        bus.knowledge_updated.connect(self.update_knowledge)

    def update_knowledge(self, k):
        def fill(lst, items, key_order):
            lst.clear()
            for e in items:
                parts = [str(e.get(k,"")) for k in key_order if e.get(k) is not None]
                QListWidgetItem(
                    self._joiner.join(p for p in parts if p),
                    lst,
                )

        fill(self.notes, k.get("notes", []), ["title", "text"])
        fill(self.factions, k.get("factions", []), ["name", "summary"])
        fill(self.sites, k.get("sites", []), ["name", "summary"])
        fill(self.tech, k.get("tech", []), ["name", "summary"])
