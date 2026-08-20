from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QFormLayout, QCheckBox, QComboBox, QPushButton,
    QMessageBox, QGroupBox, QLabel
)
from storage.settings_manager import SettingsManager
from app.hotkey_input_widget import HotkeyInputWidget


class SettingsWindow(QDialog):
    """詳細偏好設定視窗"""
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("應用程式偏好設定")
        self.resize(460, 420)

        self.sm = settings_manager
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        tab_widget = QTabWidget()

        # ── Tab 1: 錄製設定 ──────────────────────────────────────
        rec_tab = QWidget()
        rec_layout = QVBoxLayout(rec_tab)
        rec_group = QGroupBox("錄製過濾與選項")
        rec_form = QFormLayout(rec_group)

        self.chk_mouse_move = QCheckBox("記錄滑鼠移動 (Mouse Move)")
        self.chk_mouse_move.setChecked(self.sm.get("record_mouse_move", True))

        self.chk_mouse_click = QCheckBox("記錄滑鼠點擊 (Mouse Click)")
        self.chk_mouse_click.setChecked(self.sm.get("record_mouse_click", True))

        self.chk_mouse_scroll = QCheckBox("記錄滑鼠滾輪 (Mouse Scroll)")
        self.chk_mouse_scroll.setChecked(self.sm.get("record_mouse_scroll", True))

        self.chk_keyboard = QCheckBox("記錄鍵盤按鍵 (Keyboard Input)")
        self.chk_keyboard.setChecked(self.sm.get("record_keyboard", True))

        rec_form.addRow(self.chk_mouse_move)
        rec_form.addRow(self.chk_mouse_click)
        rec_form.addRow(self.chk_mouse_scroll)
        rec_form.addRow(self.chk_keyboard)

        rec_layout.addWidget(rec_group)
        rec_layout.addStretch()
        tab_widget.addTab(rec_tab, "錄製設定")

        # ── Tab 2: 全域快捷鍵 ────────────────────────────────────
        hk_tab = QWidget()
        hk_layout = QVBoxLayout(hk_tab)

        hk_group = QGroupBox("自訂全域快捷鍵 (Global Hotkeys)")
        hk_form = QFormLayout(hk_group)

        hint_lbl = QLabel("💡 點擊按鈕後直接按下想要的按鍵或組合鍵（支援 Ctrl、Shift、Alt 等修飾鍵）")
        hint_lbl.setWordWrap(True)
        hint_lbl.setStyleSheet("color: #555; font-size: 11px;")
        hk_layout.addWidget(hint_lbl)

        self.hk_rec       = HotkeyInputWidget(self.sm.get("hotkey_record",    "F6"))
        self.hk_play      = HotkeyInputWidget(self.sm.get("hotkey_play",      "F7"))
        self.hk_pause     = HotkeyInputWidget(self.sm.get("hotkey_pause",     "F8"))
        self.hk_stop      = HotkeyInputWidget(self.sm.get("hotkey_stop",      "F9"))
        self.hk_emergency = HotkeyInputWidget(self.sm.get("hotkey_emergency", "ESC"))

        hk_form.addRow("開始/停止錄製:", self.hk_rec)
        hk_form.addRow("播放腳本:", self.hk_play)
        hk_form.addRow("暫停/繼續播放:", self.hk_pause)
        hk_form.addRow("停止播放:", self.hk_stop)
        hk_form.addRow("緊急停止 (Emergency Stop):", self.hk_emergency)

        hk_layout.addWidget(hk_group)
        hk_layout.addStretch()
        tab_widget.addTab(hk_tab, "全域快捷鍵")

        # ── Tab 3: UI 與浮動提示 ─────────────────────────────────
        ui_tab = QWidget()
        ui_layout = QVBoxLayout(ui_tab)
        ui_group = QGroupBox("錄製與播放浮動提示 (Overlay HUD)")
        ui_form = QFormLayout(ui_group)

        self.chk_show_overlay = QCheckBox("顯示錄製/播放浮動提示視窗")
        self.chk_show_overlay.setChecked(self.sm.get("show_overlay", True))

        self.cbo_overlay_pos = QComboBox()
        self.cbo_overlay_pos.addItems(["右上角", "左上角", "右下角", "左下角"])
        self.cbo_overlay_pos.setCurrentText(self.sm.get("overlay_position", "右上角"))

        self.chk_minimize_tray = QCheckBox("最小化時縮小至系統工作列 (System Tray)")
        self.chk_minimize_tray.setChecked(self.sm.get("minimize_to_tray", True))

        ui_form.addRow(self.chk_show_overlay)
        ui_form.addRow("浮動提示位置:", self.cbo_overlay_pos)
        ui_form.addRow(self.chk_minimize_tray)

        ui_layout.addWidget(ui_group)
        ui_layout.addStretch()
        tab_widget.addTab(ui_tab, "介面與系統")

        main_layout.addWidget(tab_widget)

        # ── 底部按鈕 ─────────────────────────────────────────────
        btn_box = QHBoxLayout()
        save_btn = QPushButton("儲存設定")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)

        btn_box.addWidget(save_btn)
        btn_box.addWidget(cancel_btn)
        main_layout.addLayout(btn_box)

    def save_settings(self):
        # 錄製設定
        self.sm.set("record_mouse_move",   self.chk_mouse_move.isChecked())
        self.sm.set("record_mouse_click",  self.chk_mouse_click.isChecked())
        self.sm.set("record_mouse_scroll", self.chk_mouse_scroll.isChecked())
        self.sm.set("record_keyboard",     self.chk_keyboard.isChecked())

        # 快捷鍵設定
        self.sm.set("hotkey_record",    self.hk_rec.hotkey())
        self.sm.set("hotkey_play",      self.hk_play.hotkey())
        self.sm.set("hotkey_pause",     self.hk_pause.hotkey())
        self.sm.set("hotkey_stop",      self.hk_stop.hotkey())
        self.sm.set("hotkey_emergency", self.hk_emergency.hotkey())

        # UI 設定
        self.sm.set("show_overlay",     self.chk_show_overlay.isChecked())
        self.sm.set("overlay_position", self.cbo_overlay_pos.currentText())
        self.sm.set("minimize_to_tray", self.chk_minimize_tray.isChecked())

        QMessageBox.information(self, "成功", "偏好設定已成功更新！")
        self.accept()