from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRect
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class SlidingPane(QWidget):
    def __init__(self, side="left", width_px=360, title="Pane", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.side = side
        self.target_width = width_px
        self.setFixedWidth(self.target_width)
        self.setObjectName(f"{side}-pane")
        self.setStyleSheet("#left-pane, #right-pane { background:#161a1f; border:1px solid #2a2f36; }")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12,12,12,12)
        self.title = QLabel(f"<b>{title}</b>")
        self.title.setStyleSheet("color:#9ad1cc;")
        lay.addWidget(self.title)
        self.content = QVBoxLayout()
        self.content.setContentsMargins(0,8,0,0)
        lay.addLayout(self.content)
        self._open = False
        self._anim = QPropertyAnimation(self, b"geometry", duration=220)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def layout_for(self, rect: QRect):
        if self.side == "left":
            closed = QRect(-self.target_width, 0, self.target_width, rect.height())
            opened = QRect(0, 0, self.target_width, rect.height())
        else:
            closed = QRect(rect.width(), 0, self.target_width, rect.height())
            opened = QRect(rect.width()-self.target_width, 0, self.target_width, rect.height())
        return opened, closed

    def reposition(self, container_rect: QRect):
        opened, closed = self.layout_for(container_rect)
        self.setGeometry(opened if self._open else closed)

    def toggle(self, container_rect: QRect):
        self._open = not self._open
        opened, closed = self.layout_for(container_rect)
        self._anim.stop()
        self._anim.setStartValue(self.geometry())
        self._anim.setEndValue(opened if self._open else closed)
        self._anim.start()
