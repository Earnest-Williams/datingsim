from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QWidget


class CenterScene(QWidget):
    """Widget that displays a background and a foreground sprite."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background:#0e1114;")

        self.bg = QLabel(self)
        self.bg.setAlignment(Qt.AlignCenter)

        self.sprite = QLabel(self)
        self.sprite.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)

        self._bg_pix: QPixmap | None = None
        self._sprite_pix: QPixmap | None = None

    # -------------------- public API --------------------
    def set_background(self, path: str | None) -> None:
        if not path:
            self._bg_pix = None
            self.bg.clear()
            return
        pixmap = QPixmap(path)
        self._bg_pix = pixmap if not pixmap.isNull() else None
        self._rescale()

    def set_sprite(self, path: str | None) -> None:
        if not path:
            self._sprite_pix = None
            self.sprite.clear()
            return
        pixmap = QPixmap(path)
        self._sprite_pix = pixmap if not pixmap.isNull() else None
        self._rescale()

    # -------------------- QWidget overrides --------------------
    def resizeEvent(self, event):  # type: ignore[override]
        super().resizeEvent(event)
        self.bg.setGeometry(0, 0, self.width(), self.height())
        # sprite takes bottom 85% width; keeps aspect; anchored bottom-center
        self.sprite.setGeometry(
            int(self.width() * 0.075),
            int(self.height() * 0.10),
            int(self.width() * 0.85),
            int(self.height() * 0.90),
        )
        self._rescale()

    # -------------------- helpers --------------------
    def _rescale(self) -> None:
        if self._bg_pix:
            self.bg.setPixmap(
                self._bg_pix.scaled(
                    self.bg.size(),
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation,
                )
            )
        if self._sprite_pix:
            self.sprite.setPixmap(
                self._sprite_pix.scaled(
                    self.sprite.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )
