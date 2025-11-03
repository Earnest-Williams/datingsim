from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGridLayout, QListWidget, QListWidgetItem, QProgressBar

class CharacterPane(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        root = QVBoxLayout(self)
        self.name_lbl = QLabel("—")
        self.level_lbl = QLabel("Level 1")
        bars = QGridLayout()
        self.hp = QProgressBar(); self.hp.setFormat("HP %v")
        self.mp = QProgressBar(); self.mp.setFormat("MP %v")
        self.sta = QProgressBar(); self.sta.setFormat("STA %v")
        bars.addWidget(self.hp,0,0); bars.addWidget(self.mp,0,1); bars.addWidget(self.sta,0,2)

        self.attrs_lbl = QLabel("<b>Attributes</b>")
        self.attrs = QLabel("—")
        self.skills_lbl = QLabel("<b>Skills</b>")
        self.skills = QLabel("—")
        self.cond_lbl = QLabel("<b>Conditions</b>")
        self.cond = QLabel("—")

        self.inv_lbl = QLabel("<b>Inventory</b>")
        self.inv = QListWidget()

        root.addWidget(self.name_lbl)
        root.addWidget(self.level_lbl)
        root.addLayout(bars)
        root.addWidget(self.attrs_lbl); root.addWidget(self.attrs)
        root.addWidget(self.skills_lbl); root.addWidget(self.skills)
        root.addWidget(self.cond_lbl); root.addWidget(self.cond)
        root.addWidget(self.inv_lbl); root.addWidget(self.inv)

    def bind_bus(self, bus):
        bus.stats_updated.connect(self.update_stats)
        bus.inventory_updated.connect(self.update_inventory)

    def update_stats(self, s):
        self.name_lbl.setText(f"<b>{s.get('name','')}</b>")
        self.level_lbl.setText(f"Level {s.get('level',1)}")
        self.hp.setMaximum(max(s.get('hp',1),1)); self.hp.setValue(s.get('hp',1))
        self.mp.setMaximum(max(s.get('mp',0),1)); self.mp.setValue(s.get('mp',0))
        self.sta.setMaximum(max(s.get('stamina',0),1)); self.sta.setValue(s.get('stamina',0))
        attrs = s.get("attrs", {})
        self.attrs.setText(", ".join(f"{k}: {v}" for k,v in attrs.items()) or "—")
        skills = s.get("skills", {})
        self.skills.setText(", ".join(f"{k}: {v}" for k,v in skills.items()) or "—")
        conds = s.get("conditions", [])
        if isinstance(conds, dict):  # allow dict form
            conds = [f"{k}: {v}" for k,v in conds.items()]
        self.cond.setText(", ".join(map(str, conds)) or "—")

    def update_inventory(self, items):
        self.inv.clear()
        for it in items:
            name = it.get("name", it.get("id","item"))
            qty = it.get("qty", 1)
            QListWidgetItem(f"{name} ×{qty}", self.inv)
