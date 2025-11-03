from typing import Dict, Optional

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
)


class NavOverlay(QWidget):
    def __init__(self, bus, ui_strings: Optional[Dict[str, str]] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bus = bus
        ui = ui_strings or {}
        self.setObjectName("nav-overlay")
        self.setStyleSheet(
            "#nav-overlay { background: rgba(14,17,20,220); border-bottom:1px solid #2a2f36; }"
            "QLabel { color:#dde; }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        row = QHBoxLayout()
        root.addLayout(row)

        self._placeholder = ui.get("location_placeholder", "—")
        self.loc = QLabel(self._placeholder)
        row.addWidget(self.loc)

        row.addStretch(1)

        self.exits_bar = QHBoxLayout()
        row.addLayout(self.exits_bar)

        self.who_lbl = QLabel(ui.get("talk_label", " Talk: "))
        row.addWidget(self.who_lbl)
        self.who = QComboBox()
        row.addWidget(self.who)
        talk_btn = QPushButton(ui.get("talk_button", "Talk"))
        row.addWidget(talk_btn)

        talk_btn.clicked.connect(self._emit_talk)
        self.bus.nav_ready.connect(self._render)

    def _emit_talk(self):
        name = self.who.currentText().strip()
        if name:
            self.bus.talk_to.emit(name)

    def _clear_exits(self):
        while self.exits_bar.count():
            item = self.exits_bar.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _render(self, payload: dict):
        loc_label = payload.get("location") or self._placeholder
        self.loc.setText(f"<b>{loc_label}</b>")
        self._clear_exits()
        for exit_payload in payload.get("exits", []):
            button = QPushButton(exit_payload["label"])
            button.clicked.connect(
                lambda _=False, exit_id=exit_payload["id"]: self.bus.travel_chosen.emit(exit_id)
            )
            self.exits_bar.addWidget(button)
        self.who.clear()
        for name in payload.get("characters", []):
            self.who.addItem(name)
