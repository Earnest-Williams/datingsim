from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QTabWidget

class KnowledgePane(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        root = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.notes = QListWidget()
        self.factions = QListWidget()
        self.sites = QListWidget()
        self.tech = QListWidget()
        self.tabs.addTab(self.notes, "Notes")
        self.tabs.addTab(self.factions, "Factions & Enclaves")
        self.tabs.addTab(self.sites, "Sites & Rumours")
        self.tabs.addTab(self.tech, "Tech & Lore")
        root.addWidget(self.tabs)

    def bind_bus(self, bus):
        bus.knowledge_updated.connect(self.update_knowledge)

    def update_knowledge(self, k):
        def fill(lst, items, key_order):
            lst.clear()
            for e in items:
                parts = [str(e.get(k,"")) for k in key_order if e.get(k) is not None]
                QListWidgetItem(" — ".join(p for p in parts if p), lst)

        fill(self.notes, k.get("notes", []), ["title", "text"])
        fill(self.factions, k.get("factions", []), ["name", "summary"])
        fill(self.sites, k.get("sites", []), ["name", "summary"])
        fill(self.tech, k.get("tech", []), ["name", "summary"])
