from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QApplication
from PySide6.QtGui import QFont, QColor

class FloatingOverlayWindow(QWidget):
    """
    錄製與播放時發生的獨立小型浮動提示視窗：
    - Always on top (Qt.WindowStaysOnTopHint)
    - 無邊框 (Qt.FramelessWindowHint)
    - 不佔用工作列 (Qt.Tool)
    - 可拖曳位置
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.drag_position = QPoint()

        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        # Container Widget for Styling
        self.container = QWidget(self)
        self.container.setStyleSheet("""
            QWidget {
                background-color: rgba(24, 28, 36, 0.90);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
            }
        """)

        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(10, 6, 10, 6)

        # 狀態紅綠點/標示
        self.dot_label = QLabel("●", self.container)
        self.dot_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.dot_label.setStyleSheet("color: #FF4D4F;") # 紅色代表錄製

        # 文字內容
        self.text_label = QLabel("正在錄製 (按 F6 停止)", self.container)
        self.text_label.setFont(QFont("Microsoft JhengHei UI", 10, QFont.Weight.Bold))
        self.text_label.setStyleSheet("color: #FFFFFF;")

        container_layout.addWidget(self.dot_label)
        container_layout.addWidget(self.text_label)

        layout.addWidget(self.container)
        self.setLayout(layout)

        self.adjust_position("右上角")

    def show_recording(self, hotkey_stop="F6"):
        self.dot_label.setText("●")
        self.dot_label.setStyleSheet("color: #FF4D4F;")
        self.text_label.setText(f"錄製中 (按 {hotkey_stop} 停止)")
        self.show()

    def show_playback(self, current_loop=1, total_loops=1, hotkey_stop="F9"):
        self.dot_label.setText("▶")
        self.dot_label.setStyleSheet("color: #52C41A;")
        loop_str = f"{current_loop}/{total_loops}" if total_loops > 0 else f"{current_loop}/無限"
        self.text_label.setText(f"播放中 [第 {loop_str} 次] (按 {hotkey_stop} 停止)")
        self.show()

    def update_text(self, text: str):
        self.text_label.setText(text)

    def adjust_position(self, pos_str: str = "右上角"):
        screen = QApplication.primaryScreen()
        if not screen:
            return
        rect = screen.availableGeometry()
        w, h = 240, 50

        if pos_str == "左上角":
            self.move(rect.x() + 20, rect.y() + 20)
        elif pos_str == "右上角":
            self.move(rect.x() + rect.width() - w - 20, rect.y() + 20)
        elif pos_str == "左下角":
            self.move(rect.x() + 20, rect.y() + rect.height() - h - 20)
        elif pos_str == "右下角":
            self.move(rect.x() + rect.width() - w - 20, rect.y() + rect.height() - h - 20)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()