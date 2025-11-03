from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
)


class NavOverlay(QWidget):
    def __init__(self, bus, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bus = bus
        self.setObjectName("nav-overlay")
        self.setStyleSheet(
            "#nav-overlay { background: rgba(14,17,20,220); border-bottom:1px solid #2a2f36; }"
            "QLabel { color:#dde; }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        row = QHBoxLayout()
        root.addLayout(row)

        self.loc = QLabel("—")
        row.addWidget(self.loc)

        row.addStretch(1)

        self.exits_bar = QHBoxLayout()
        row.addLayout(self.exits_bar)

        self.who_lbl = QLabel(" Talk: ")
        row.addWidget(self.who_lbl)
        self.who = QComboBox()
        row.addWidget(self.who)
        talk_btn = QPushButton("Talk")
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
        self.loc.setText(f"<b>{payload.get('location', '—')}</b>")
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
