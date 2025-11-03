from typing import Any, Dict, Optional

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QGridLayout,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
)


class CharacterPane(QWidget):
    def __init__(self, *args, ui_strings: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(*args, **kwargs)
        ui = ui_strings or {}
        self._placeholder = ui.get("placeholder", "—")
        self._list_join = ui.get("list_join", ", ")
        self._level_format = ui.get("level_format", "Level {level}")
        self._hp_format = ui.get("hp_format", "HP %v")
        self._mp_format = ui.get("mp_format", "MP %v")
        self._stamina_format = ui.get("stamina_format", "STA %v")
        self._inventory_format = ui.get(
            "inventory_entry_format", "{name} ×{qty}"
        )

        root = QVBoxLayout(self)
        self.name_lbl = QLabel(self._placeholder)
        self.level_lbl = QLabel(self._level_format.format(level=1))
        bars = QGridLayout()
        self.hp = QProgressBar()
        self.hp.setFormat(self._hp_format)
        self.mp = QProgressBar()
        self.mp.setFormat(self._mp_format)
        self.sta = QProgressBar()
        self.sta.setFormat(self._stamina_format)
        bars.addWidget(self.hp, 0, 0)
        bars.addWidget(self.mp, 0, 1)
        bars.addWidget(self.sta, 0, 2)

        self.attrs_lbl = QLabel(f"<b>{ui.get('attributes_title', 'Attributes')}</b>")
        self.attrs = QLabel(self._placeholder)
        self.skills_lbl = QLabel(f"<b>{ui.get('skills_title', 'Skills')}</b>")
        self.skills = QLabel(self._placeholder)
        self.cond_lbl = QLabel(f"<b>{ui.get('conditions_title', 'Conditions')}</b>")
        self.cond = QLabel(self._placeholder)

        self.inv_lbl = QLabel(f"<b>{ui.get('inventory_title', 'Inventory')}</b>")
        self.inv = QListWidget()

        root.addWidget(self.name_lbl)
        root.addWidget(self.level_lbl)
        root.addLayout(bars)
        root.addWidget(self.attrs_lbl)
        root.addWidget(self.attrs)
        root.addWidget(self.skills_lbl)
        root.addWidget(self.skills)
        root.addWidget(self.cond_lbl)
        root.addWidget(self.cond)
        root.addWidget(self.inv_lbl)
        root.addWidget(self.inv)

    def bind_bus(self, bus):
        bus.stats_updated.connect(self.update_stats)
        bus.inventory_updated.connect(self.update_inventory)

    def update_stats(self, s):
        self.name_lbl.setText(f"<b>{s.get('name', '')}</b>")
        self.level_lbl.setText(self._level_format.format(level=s.get("level", 1)))
        self.hp.setMaximum(max(s.get("hp", 1), 1))
        self.hp.setValue(s.get("hp", 1))
        self.mp.setMaximum(max(s.get("mp", 0), 1))
        self.mp.setValue(s.get("mp", 0))
        self.sta.setMaximum(max(s.get("stamina", 0), 1))
        self.sta.setValue(s.get("stamina", 0))
        attrs = s.get("attrs", {})
        attrs_text = self._list_join.join(f"{k}: {v}" for k, v in attrs.items())
        self.attrs.setText(attrs_text or self._placeholder)
        skills = s.get("skills", {})
        skills_text = self._list_join.join(f"{k}: {v}" for k, v in skills.items())
        self.skills.setText(skills_text or self._placeholder)
        conds = s.get("conditions", [])
        if isinstance(conds, dict):
            conds = [f"{k}: {v}" for k, v in conds.items()]
        cond_text = self._list_join.join(map(str, conds))
        self.cond.setText(cond_text or self._placeholder)

    def update_inventory(self, items):
        self.inv.clear()
        for it in items:
            name = it.get("name", it.get("id", "item"))
            qty = it.get("qty", 1)
            QListWidgetItem(
                self._inventory_format.format(name=name, qty=qty),
                self.inv,
            )
