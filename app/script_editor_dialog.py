from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, 
    QPushButton, QMessageBox
)
from PySide6.QtGui import QFont
from core.events import MacroEvent, EventType

class EventEditorDialog(QDialog):
    """巨集事件編輯/新增對話框"""
    def __init__(self, event: MacroEvent, parent=None):
        super().__init__(parent)
        self.setWindowTitle("編輯巨集事件")
        self.resize(320, 280)

        self.event = event
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.type_combo = QComboBox()
        self.type_combo.addItems([
            EventType.MOUSE_MOVE.value,
            EventType.MOUSE_PRESS.value,
            EventType.MOUSE_RELEASE.value,
            EventType.MOUSE_SCROLL.value,
            EventType.KEY_PRESS.value,
            EventType.KEY_RELEASE.value
        ])
        self.type_combo.setCurrentText(self.event.type.value if hasattr(self.event.type, 'value') else str(self.event.type))
        form_layout.addRow("事件類型:", self.type_combo)

        self.delay_spin = QDoubleSpinBox()
        self.delay_spin.setRange(0.001, 3600.0)
        self.delay_spin.setDecimals(3)
        self.delay_spin.setSingleStep(0.05)
        self.delay_spin.setValue(self.event.delay)
        form_layout.addRow("延遲時間 (秒):", self.delay_spin)

        self.x_spin = QSpinBox()
        self.x_spin.setRange(0, 99999)
        self.x_spin.setValue(self.event.x)
        form_layout.addRow("X 座標:", self.x_spin)

        self.y_spin = QSpinBox()
        self.y_spin.setRange(0, 99999)
        self.y_spin.setValue(self.event.y)
        form_layout.addRow("Y 座標:", self.y_spin)

        self.key_input = QLineEdit()
        current_key_val = self.event.key or self.event.button or ""
        self.key_input.setText(str(current_key_val))
        form_layout.addRow("按鍵/按鈕:", self.key_input)

        layout.addLayout(form_layout)

        btn_box = QHBoxLayout()
        ok_btn = QPushButton("確定")
        ok_btn.clicked.connect(self.save_and_accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)

        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)
        layout.addLayout(btn_box)

    def save_and_accept(self):
        try:
            self.event.type = EventType(self.type_combo.currentText())
            self.event.delay = self.delay_spin.value()
            self.event.x = self.x_spin.value()
            self.event.y = self.y_spin.value()

            key_val = self.key_input.text().strip()
            if self.event.type in (EventType.KEY_PRESS, EventType.KEY_RELEASE):
                self.event.key = key_val
                self.event.button = None
            elif self.event.type in (EventType.MOUSE_PRESS, EventType.MOUSE_RELEASE):
                self.event.button = key_val
                self.event.key = None

            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "錯誤", f"儲存事件設定失敗: {e}")