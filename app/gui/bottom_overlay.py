from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRect
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout

class BottomOverlay(QWidget):
    def __init__(self, bus, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bus = bus
        self.setObjectName("bottom-overlay")
        self.setStyleSheet("""
        #bottom-overlay { background: rgba(14,17,20,220); border-top: 1px solid #2a2f36; }
        QLabel#toast { color:#f6c177; font-style:italic; }
        QLabel#speaker { color:#9ad1cc; font-weight:600; }
        QLabel#text { color:#eef; }
        QPushButton { padding:8px 12px; border:1px solid #3a3f46; background:#1b2027; color:#dde; }
        QPushButton:hover { border-color:#9ad1cc; }
        """)
        self.toast = QLabel(wordWrap=True, objectName="toast")
        self.toast.setVisible(False)
        self.speaker = QLabel(objectName="speaker")
        self.text = QLabel(wordWrap=True, objectName="text")
        self.choices = QHBoxLayout()
        v = QVBoxLayout(self)
        v.setContentsMargins(16,12,16,12)
        v.addWidget(self.toast)
        v.addWidget(self.speaker)
        v.addWidget(self.text)
        v.addLayout(self.choices)
        self.setVisible(False)
        self._anim = QPropertyAnimation(self, b"geometry", duration=180)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

        self.bus.dialogue_ready.connect(self.show_dialogue)
        self.bus.toast.connect(self.show_toast)

    def resize_to(self, rect: QRect, height_px: int = 220):
        self.setGeometry(0, rect.height(), rect.width(), height_px)

    def show_panel(self, rect: QRect):
        self.setVisible(True)
        self._anim.stop()
        self._anim.setStartValue(QRect(0, rect.height(), rect.width(), self.height()))
        self._anim.setEndValue(QRect(0, rect.height()-self.height(), rect.width(), self.height()))
        self._anim.start()

    def clear_choices(self):
        while self.choices.count():
            item = self.choices.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def show_dialogue(self, payload: dict):
        self.speaker.setText(payload.get("speaker", ""))
        self.text.setText(payload.get("text", ""))
        self.clear_choices()
        for opt in payload.get("options", []):
            b = QPushButton(opt["label"])
            b.clicked.connect(lambda _, oid=opt["id"]: self.bus.option_chosen.emit(oid))
            self.choices.addWidget(b)
        self.show_panel(self.parent().rect())

    def show_toast(self, message: str):
        self.toast.setVisible(bool(message))
        self.toast.setText(message)
