from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction, QPixmap, QColor, QPainter

def create_default_tray_icon() -> QIcon:
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setBrush(QColor(24, 144, 255))
    painter.setPen(QColor(255, 255, 255))
    painter.drawEllipse(2, 2, 28, 28)
    painter.end()
    return QIcon(pixmap)

class MacroSystemTray(QSystemTrayIcon):
    """Windows 右下角系統工作列圖示與快顯選單"""
    def __init__(self, main_window, parent=None):
        icon = create_default_tray_icon()
        super().__init__(icon, parent)
        self.main_window = main_window
        self.setToolTip("Windows 巨集錄製器 (巨集/自動鍵盤滑鼠)")

        self.init_menu()

    def init_menu(self):
        menu = QMenu()

        act_show = QAction("顯示主視窗", self)
        act_show.triggered.connect(self.main_window.show_normal_and_raise)

        act_record = QAction("開始/停止錄製 (F6)", self)
        act_record.triggered.connect(self.main_window.toggle_record)

        act_play = QAction("播放腳本 (F7)", self)
        act_play.triggered.connect(self.main_window.start_playback)

        act_stop = QAction("停止播放 (F9)", self)
        act_stop.triggered.connect(self.main_window.stop_playback)

        act_exit = QAction("退出應用程式", self)
        act_exit.triggered.connect(self.main_window.close_application)

        menu.addAction(act_show)
        menu.addSeparator()
        menu.addAction(act_record)
        menu.addAction(act_play)
        menu.addAction(act_stop)
        menu.addSeparator()
        menu.addAction(act_exit)

        self.setContextMenu(menu)
        self.activated.connect(self._on_tray_activated)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.main_window.show_normal_and_raise()