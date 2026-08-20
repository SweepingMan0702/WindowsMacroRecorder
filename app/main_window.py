# PySide6 主視窗模組 (主控制面板、事件列表、狀態列)
import os, sys, time
from typing import Optional
from PySide6.QtCore import Qt, QTimer, Slot, QPoint
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QPushButton, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QFileDialog, QMessageBox, QFrame, QSplitter, QStatusBar, QApplication
)
from PySide6.QtGui import QFont, QColor, QCursor

from core.events import MacroEvent, EventType
from core.recorder import MacroRecorder
from core.player import MacroPlayerThread
from core.hotkeys import GlobalHotkeyManager
from models.script import MacroScript, PlaybackSettings
from storage.script_manager import ScriptManager
from storage.settings_manager import SettingsManager
from app.overlay import FloatingOverlayWindow
from app.settings_window import SettingsWindow
from app.system_tray import MacroSystemTray
from app.script_editor_dialog import EventEditorDialog
from utils.logger import logger
from utils.windows import is_admin, release_all_keys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Windows 巨集錄製器 (Mouse & Keyboard Macro Recorder)")
        self.resize(1000, 720)
        self.setMinimumSize(850, 600)

        # 核心組件實例化
        self.sm = SettingsManager()
        self.script_mgr = ScriptManager()
        self.recorder = MacroRecorder()
        self.player_thread: Optional[MacroPlayerThread] = None
        self.hotkey_mgr = GlobalHotkeyManager()

        # 當前腳本與狀態
        self.current_script = MacroScript(name="新腳本")
        self.current_file_path: Optional[str] = None
        self.status = "待機"

        # UI 組件初始化
        self.overlay = FloatingOverlayWindow()
        self.tray_icon = MacroSystemTray(self)
        self.tray_icon.show()

        # 介面建置
        self.init_ui()
        self.setup_timer()
        self.setup_hotkeys()

        # 權限檢查與提示
        if not is_admin():
            logger.warning("提示：程式目前非以系統管理員身分執行，部分以 Admin 執行的遊戲或軟體可能無法接收錄製/播放鍵鼠事件。")

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 1. 頂部狀態與主控制面板
        top_panel = self.create_control_panel()
        main_layout.addWidget(top_panel)

        # 2. 中間 Splitter: 左側播放設定、右側腳本事件列表
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左側播放與循環設定面板
        settings_panel = self.create_playback_settings_panel()
        splitter.addWidget(settings_panel)

        # 右側腳本事件表格與編輯列
        table_panel = self.create_events_table_panel()
        splitter.addWidget(table_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        main_layout.addWidget(splitter, stretch=1)

        # 3. 底部狀態列
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_lbl = QLabel("狀態: 待機 | 系統管理員: " + ("是" if is_admin() else "否"))
        self.mouse_pos_lbl = QLabel("滑鼠座標: X=0, Y=0")
        self.status_bar.addWidget(self.status_lbl, 1)
        self.status_bar.addPermanentWidget(self.mouse_pos_lbl)

    def create_control_panel(self) -> QGroupBox:
        group = QGroupBox("控制面板")
        layout = QVBoxLayout(group)

        # 狀態顯示列
        status_box = QHBoxLayout()
        self.lbl_status_badge = QLabel("● 狀態：待機")
        self.lbl_status_badge.setFont(QFont("Microsoft JhengHei UI", 12, QFont.Weight.Bold))
        self.lbl_status_badge.setStyleSheet("color: #1890FF;")

        self.lbl_time = QLabel("錄製時間：00:00.0")
        self.lbl_events_count = QLabel("事件數量：0")
        self.lbl_script_name = QLabel("目前腳本：未儲存 (新腳本)")

        status_box.addWidget(self.lbl_status_badge)
        status_box.addSpacing(20)
        status_box.addWidget(self.lbl_time)
        status_box.addSpacing(15)
        status_box.addWidget(self.lbl_events_count)
        status_box.addStretch()
        status_box.addWidget(self.lbl_script_name)
        layout.addLayout(status_box)

        # 控制按鈕列
        btn_layout = QHBoxLayout()
        self.btn_rec = QPushButton("● 開始錄製 (F6)")
        self.btn_rec.setFixedHeight(38)
        self.btn_rec.setStyleSheet("background-color: #FF4D4F; color: white; font-weight: bold;")
        self.btn_rec.clicked.connect(self.toggle_record)

        self.btn_pause_rec = QPushButton("❚❚ 暫停錄製")
        self.btn_pause_rec.setFixedHeight(38)
        self.btn_pause_rec.setEnabled(False)
        self.btn_pause_rec.clicked.connect(self.pause_record)

        self.btn_stop_rec = QPushButton("■ 停止錄製")
        self.btn_stop_rec.setFixedHeight(38)
        self.btn_stop_rec.setEnabled(False)
        self.btn_stop_rec.clicked.connect(self.stop_record)

        self.btn_play = QPushButton("▶ 開始播放 (F7)")
        self.btn_play.setFixedHeight(38)
        self.btn_play.setStyleSheet("background-color: #52C41A; color: white; font-weight: bold;")
        self.btn_play.clicked.connect(self.start_playback)

        self.btn_pause_play = QPushButton("❚❚ 暫停播放 (F8)")
        self.btn_pause_play.setFixedHeight(38)
        self.btn_pause_play.setEnabled(False)
        self.btn_pause_play.clicked.connect(self.toggle_pause_playback)

        self.btn_stop_play = QPushButton("■ 停止播放 (F9)")
        self.btn_stop_play.setFixedHeight(38)
        self.btn_stop_play.setEnabled(False)
        self.btn_stop_play.clicked.connect(self.stop_playback)

        self.btn_settings = QPushButton("⚙ 設定")
        self.btn_settings.setFixedHeight(38)
        self.btn_settings.clicked.connect(self.open_settings)

        btn_layout.addWidget(self.btn_rec)
        btn_layout.addWidget(self.btn_pause_rec)
        btn_layout.addWidget(self.btn_stop_rec)
        btn_layout.addSpacing(10)
        btn_layout.addWidget(self.btn_play)
        btn_layout.addWidget(self.btn_pause_play)
        btn_layout.addWidget(self.btn_stop_play)
        btn_layout.addSpacing(10)
        btn_layout.addWidget(self.btn_settings)

        layout.addLayout(btn_layout)
        return group

    def create_playback_settings_panel(self) -> QGroupBox:
        group = QGroupBox("播放與循環設定")
        layout = QFormLayout(group)

        # 播放速度
        self.cbo_speed = QComboBox()
        self.cbo_speed.addItems(["0.25x (極慢)", "0.5x (半速)", "0.75x", "1.0x (原速)", "1.5x", "2.0x (雙倍)", "4.0x (四倍)"])
        self.cbo_speed.setCurrentIndex(3) # 預設 1.0x
        self.cbo_speed.currentIndexChanged.connect(self.update_playback_settings_from_ui)

        # 全域額外延遲 (ms)
        self.spn_extra_delay = QSpinBox()
        self.spn_extra_delay.setRange(0, 60000)
        self.spn_extra_delay.setSuffix(" ms")
        self.spn_extra_delay.setSingleStep(50)
        self.spn_extra_delay.valueChanged.connect(self.update_playback_settings_from_ui)

        # 固定事件間隔模式 (ms)
        self.spn_fixed_interval = QSpinBox()
        self.spn_fixed_interval.setRange(-1, 60000)
        self.spn_fixed_interval.setSpecialValueText("使用錄製原始間隔")
        self.spn_fixed_interval.setSuffix(" ms")
        self.spn_fixed_interval.setValue(-1)
        self.spn_fixed_interval.valueChanged.connect(self.update_playback_settings_from_ui)

        # 循環次數 (0 表示無限循環)
        self.spn_loops = QSpinBox()
        self.spn_loops.setRange(0, 999999)
        self.spn_loops.setSpecialValueText("無限循環 (∞)")
        self.spn_loops.setValue(1)
        self.spn_loops.valueChanged.connect(self.update_playback_settings_from_ui)

        # 每輪循環間隔 (秒)
        self.spn_loop_interval = QDoubleSpinBox()
        self.spn_loop_interval.setRange(0.0, 3600.0)
        self.spn_loop_interval.setSuffix(" 秒")
        self.spn_loop_interval.setValue(1.0)
        self.spn_loop_interval.valueChanged.connect(self.update_playback_settings_from_ui)

        layout.addRow("播放速度倍率:", self.cbo_speed)
        layout.addRow("全域額外延遲:", self.spn_extra_delay)
        layout.addRow("固定事件間隔:", self.spn_fixed_interval)
        layout.addRow("播放循環次數:", self.spn_loops)
        layout.addRow("每輪間隔時間:", self.spn_loop_interval)

        return group

    def create_events_table_panel(self) -> QGroupBox:
        group = QGroupBox("巨集腳本事件列表")
        layout = QVBoxLayout(group)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["#", "事件類型", "操作/按鍵", "X 座標", "Y 座標", "延遲 (秒)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        layout.addWidget(self.table)

        # 編輯按鈕列
        action_layout = QHBoxLayout()
        btn_add = QPushButton("新增事件")
        btn_add.clicked.connect(self.add_event_dialog)

        btn_edit = QPushButton("編輯事件")
        btn_edit.clicked.connect(self.edit_selected_event)

        btn_del = QPushButton("刪除選取")
        btn_del.clicked.connect(self.delete_selected_event)

        btn_up = QPushButton("▲ 上移")
        btn_up.clicked.connect(self.move_event_up)

        btn_down = QPushButton("▼ 下移")
        btn_down.clicked.connect(self.move_event_down)

        btn_clear = QPushButton("清空全部")
        btn_clear.clicked.connect(self.clear_all_events)

        action_layout.addWidget(btn_add)
        action_layout.addWidget(btn_edit)
        action_layout.addWidget(btn_del)
        action_layout.addWidget(btn_up)
        action_layout.addWidget(btn_down)
        action_layout.addWidget(btn_clear)
        layout.addLayout(action_layout)

        # 檔案管理按鈕列
        file_layout = QHBoxLayout()
        btn_new = QPushButton("新腳本")
        btn_new.clicked.connect(self.new_script)

        btn_open = QPushButton("開啟腳本 (.json)")
        btn_open.clicked.connect(self.open_script)

        btn_save = QPushButton("儲存腳本")
        btn_save.clicked.connect(self.save_script)

        btn_save_as = QPushButton("另存新檔...")
        btn_save_as.clicked.connect(self.save_script_as)

        file_layout.addWidget(btn_new)
        file_layout.addWidget(btn_open)
        file_layout.addWidget(btn_save)
        file_layout.addWidget(btn_save_as)
        layout.addLayout(file_layout)

        return group

    def setup_timer(self):
        # 定時更新計時器與目前滑鼠座標
        self.ui_timer = QTimer(self)
        self.ui_timer.setInterval(100) # 100ms 更新頻率
        self.ui_timer.timeout.connect(self.on_ui_timer_tick)
        self.ui_timer.start()

    def setup_hotkeys(self):
        # 全域熱鍵連接 Signal
        self.hotkey_mgr.record_toggle_triggered.connect(self.toggle_record)
        self.hotkey_mgr.play_toggle_triggered.connect(self.start_playback)
        self.hotkey_mgr.pause_toggle_triggered.connect(self.toggle_pause_playback)
        self.hotkey_mgr.stop_triggered.connect(self.stop_playback)
        self.hotkey_mgr.emergency_stop_triggered.connect(self.emergency_stop)

        self.reload_hotkeys()

    def reload_hotkeys(self):
        rec_hk = self.sm.get("hotkey_record", "F6")
        play_hk = self.sm.get("hotkey_play", "F7")
        pause_hk = self.sm.get("hotkey_pause", "F8")
        stop_hk = self.sm.get("hotkey_stop", "F9")
        emergency_hk = self.sm.get("hotkey_emergency", "ESC")

        self.hotkey_mgr.update_hotkeys(
            record_key=rec_hk,
            play_key=play_hk,
            pause_key=pause_hk,
            stop_key=stop_hk,
            emergency_key=emergency_hk
        )

        if self.recorder.is_recording:
            self.btn_rec.setText(f"● 停止錄製 ({rec_hk})")
        else:
            self.btn_rec.setText(f"● 開始錄製 ({rec_hk})")

        self.btn_play.setText(f"▶ 開始播放 ({play_hk})")
        self.btn_pause_play.setText(f"❚❚ 暫停播放 ({pause_hk})")
        self.btn_stop_play.setText(f"■ 停止播放 ({stop_hk})")

    # --- UI 定時與更新邏輯 ---
    def on_ui_timer_tick(self):
        # 更新即時滑鼠座標
        pos = QCursor.pos()
        self.mouse_pos_lbl.setText(f"滑鼠座標: X={pos.x()}, Y={pos.y()}")

        # 錄製時更新時間
        if self.recorder.is_recording and not self.recorder.is_paused:
            elapsed = self.recorder.get_elapsed_time()
            mins = int(elapsed // 60)
            secs = int(elapsed % 60)
            tenths = int((elapsed * 10) % 10)
            self.lbl_time.setText(f"錄製時間：{mins:02d}:{secs:02d}.{tenths}")
            self.lbl_events_count.setText(f"事件數量：{len(self.recorder.events)}")

    def update_events_table(self):
        self.table.setRowCount(0)
        events = self.current_script.events
        self.lbl_events_count.setText(f"事件數量：{len(events)}")

        for idx, event in enumerate(events):
            self.table.insertRow(idx)
            self.table.setItem(idx, 0, QTableWidgetItem(str(idx + 1)))

            # 事件類型中文標籤
            etype_map = {
                EventType.MOUSE_MOVE: "滑鼠移動",
                EventType.MOUSE_PRESS: "滑鼠按下",
                EventType.MOUSE_RELEASE: "滑鼠放開",
                EventType.MOUSE_SCROLL: "滑鼠滾輪",
                EventType.KEY_PRESS: "鍵盤按下",
                EventType.KEY_RELEASE: "鍵盤放開"
            }
            etype_str = etype_map.get(event.type, str(event.type))
            self.table.setItem(idx, 1, QTableWidgetItem(etype_str))

            # 操作/按鍵內容
            op_str = event.key or event.button or (f"滾輪({event.dx},{event.dy})" if event.dx or event.dy else "-")
            self.table.setItem(idx, 2, QTableWidgetItem(str(op_str)))

            self.table.setItem(idx, 3, QTableWidgetItem(str(event.x)))
            self.table.setItem(idx, 4, QTableWidgetItem(str(event.y)))
            self.table.setItem(idx, 5, QTableWidgetItem(f"{event.delay:.3f}s"))

    # --- 錄製控制邏輯 ---
    def toggle_record(self):
        if self.recorder.is_recording:
            self.stop_record()
        else:
            self.start_record()

    def start_record(self):
        if self.player_thread and self.player_thread.isRunning():
            QMessageBox.warning(self, "提示", "巨集正在播放中，請先停止播放後再開始錄製。")
            return

        # 套用錄製設定
        self.recorder.record_mouse_move = self.sm.get("record_mouse_move", True)
        self.recorder.record_mouse_click = self.sm.get("record_mouse_click", True)
        self.recorder.record_mouse_scroll = self.sm.get("record_mouse_scroll", True)
        self.recorder.record_keyboard = self.sm.get("record_keyboard", True)

        # 設定需過濾的本程式快捷鍵
        self.recorder.set_ignored_hotkeys([
            self.sm.get("hotkey_record", "F6"),
            self.sm.get("hotkey_play", "F7"),
            self.sm.get("hotkey_pause", "F8"),
            self.sm.get("hotkey_stop", "F9"),
            self.sm.get("hotkey_emergency", "ESC")
        ])

        self.recorder.start()

        rec_hk = self.sm.get("hotkey_record", "F6")
        self.lbl_status_badge.setText("● 狀態：錄製中")
        self.lbl_status_badge.setStyleSheet("color: #FF4D4F;")
        self.btn_rec.setText(f"● 停止錄製 ({rec_hk})")
        self.btn_pause_rec.setEnabled(True)
        self.btn_stop_rec.setEnabled(True)
        self.btn_play.setEnabled(False)

        if self.sm.get("show_overlay", True):
            pos_str = self.sm.get("overlay_position", "右上角")
            self.overlay.adjust_position(pos_str)
            self.overlay.show_recording(rec_hk)

        logger.info("使用者啟動巨集錄製")

    def pause_record(self):
        if self.recorder.is_paused:
            self.recorder.resume() # 恢復
            self.btn_pause_rec.setText("❚❚ 暫停錄製")
            self.lbl_status_badge.setText("● 狀態：錄製中")
            self.lbl_status_badge.setStyleSheet("color: #FF4D4F;")
        else:
            self.recorder.pause()
            self.btn_pause_rec.setText("▶ 繼續錄製")
            self.lbl_status_badge.setText("● 狀態：已暫停錄製")
            self.lbl_status_badge.setStyleSheet("color: #FAAD14;")

    def stop_record(self):
        events = self.recorder.stop()
        self.current_script.events = events
        self.update_events_table()

        rec_hk = self.sm.get("hotkey_record", "F6")
        self.lbl_status_badge.setText("● 狀態：待機")
        self.lbl_status_badge.setStyleSheet("color: #1890FF;")
        self.btn_rec.setText(f"● 開始錄製 ({rec_hk})")
        self.btn_pause_rec.setEnabled(False)
        self.btn_pause_rec.setText("❚❚ 暫停錄製")
        self.btn_stop_rec.setEnabled(False)
        self.btn_play.setEnabled(True)

        self.overlay.hide()
        QMessageBox.information(self, "錄製完成", f"錄製結束，共儲存 {len(events)} 個事件腳本。")

    # --- 播放控制邏輯 ---
    def start_playback(self):
        if self.recorder.is_recording:
            QMessageBox.warning(self, "提示", "目前正在錄製中，請先停止錄製再開始播放。")
            return

        if len(self.current_script.events) == 0:
            QMessageBox.warning(self, "提示", "目前腳本事件列表為空，請先錄製或開啟腳本。")
            return

        # 更新 UI 設定至 PlaybackSettings
        self.update_playback_settings_from_ui()

        # 啟動背景 QThread 播放器
        self.player_thread = MacroPlayerThread(self.current_script, self.current_script.settings)
        self.player_thread.progress_updated.connect(self.on_playback_progress)
        self.player_thread.status_changed.connect(self.on_playback_status_changed)
        self.player_thread.finished_playback.connect(self.on_playback_finished)
        self.player_thread.error_occurred.connect(self.on_playback_error)

        self.player_thread.start()

        self.lbl_status_badge.setText("● 狀態：播放中")
        self.lbl_status_badge.setStyleSheet("color: #52C41A;")
        self.btn_play.setEnabled(False)
        self.btn_rec.setEnabled(False)
        self.btn_pause_play.setEnabled(True)
        self.btn_stop_play.setEnabled(True)

        if self.sm.get("show_overlay", True):
            pos_str = self.sm.get("overlay_position", "右上角")
            self.overlay.adjust_position(pos_str)
            self.overlay.show_playback(
                current_loop=1,
                total_loops=self.current_script.settings.loops,
                hotkey_stop=self.sm.get("hotkey_stop", "F9")
            )

    def toggle_pause_playback(self):
        if not self.player_thread or not self.player_thread.isRunning():
            return

        pause_hk = self.sm.get("hotkey_pause", "F8")
        if self.player_thread._is_paused:
            self.player_thread.resume()
            self.btn_pause_play.setText(f"❚❚ 暫停播放 ({pause_hk})")
            self.lbl_status_badge.setText("● 狀態：播放中")
            self.lbl_status_badge.setStyleSheet("color: #52C41A;")
        else:
            self.player_thread.pause()
            self.btn_pause_play.setText(f"▶ 繼續播放 ({pause_hk})")
            self.lbl_status_badge.setText("● 狀態：已暫停播放")
            self.lbl_status_badge.setStyleSheet("color: #FAAD14;")

    def stop_playback(self):
        if self.player_thread and self.player_thread.isRunning():
            self.player_thread.stop()
            self.player_thread.wait() # 等待執行緒結束

    def emergency_stop(self):
        logger.info("全域緊急停止 (ESC) 被觸發！")
        if self.recorder.is_recording:
            self.stop_record()
        if self.player_thread and self.player_thread.isRunning():
            self.player_thread.stop()

        release_all_keys()
        self.overlay.hide()
        self.lbl_status_badge.setText("● 狀態：已緊急停止")
        self.lbl_status_badge.setStyleSheet("color: #FF4D4F;")

    @Slot(int, int, int, int)
    def on_playback_progress(self, idx: int, total: int, loop: int, total_loops: int):
        # 高亮目前播放的表格列
        if idx - 1 < self.table.rowCount():
            self.table.selectRow(idx - 1)

        if self.sm.get("show_overlay", True):
            self.overlay.show_playback(
                current_loop=loop,
                total_loops=total_loops,
                hotkey_stop=self.sm.get("hotkey_stop", "F9")
            )

    @Slot(str)
    def on_playback_status_changed(self, status: str):
        self.status_bar.showMessage(f"播放狀態: {status}")

    @Slot()
    def on_playback_finished(self):
        play_hk = self.sm.get("hotkey_play", "F7")
        self.lbl_status_badge.setText("● 狀態：待機")
        self.lbl_status_badge.setStyleSheet("color: #1890FF;")
        self.btn_play.setText(f"▶ 開始播放 ({play_hk})")
        self.btn_play.setEnabled(True)
        self.btn_rec.setEnabled(True)
        self.btn_pause_play.setEnabled(False)
        self.btn_stop_play.setEnabled(False)
        self.overlay.hide()
        self.status_bar.showMessage("播放已完成")

    @Slot(str)
    def on_playback_error(self, err_msg: str):
        QMessageBox.critical(self, "播放錯誤", err_msg)

    # --- 播放設定 UI 與模型同步 ---
    def update_playback_settings_from_ui(self):
        speed_map = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 4.0]
        speed_val = speed_map[self.cbo_speed.currentIndex()]
        
        self.current_script.settings.speed = speed_val
        self.current_script.settings.extra_delay_ms = self.spn_extra_delay.value()
        self.current_script.settings.fixed_interval_ms = self.spn_fixed_interval.value()
        self.current_script.settings.loops = self.spn_loops.value()
        self.current_script.settings.loop_interval_sec = self.spn_loop_interval.value()

    # --- 腳本事件列表編輯功能 ---
    def add_event_dialog(self):
        new_event = MacroEvent(type=EventType.MOUSE_PRESS, x=500, y=300, delay=0.1)
        dlg = EventEditorDialog(new_event, self)
        if dlg.exec():
            self.current_script.events.append(new_event)
            self.update_events_table()

    def edit_selected_event(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.current_script.events):
            QMessageBox.warning(self, "提示", "請先點擊選取要編輯的事件。")
            return
        event = self.current_script.events[row]
        dlg = EventEditorDialog(event, self)
        if dlg.exec():
            self.update_events_table()

    def delete_selected_event(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.current_script.events):
            QMessageBox.warning(self, "提示", "請先選取要刪除的事件。")
            return
        self.current_script.events.pop(row)
        self.update_events_table()

    def move_event_up(self):
        row = self.table.currentRow()
        if row <= 0:
            return
        events = self.current_script.events
        events[row], events[row - 1] = events[row - 1], events[row]
        self.update_events_table()
        self.table.selectRow(row - 1)

    def move_event_down(self):
        row = self.table.currentRow()
        events = self.current_script.events
        if row < 0 or row >= len(events) - 1:
            return
        events[row], events[row + 1] = events[row + 1], events[row]
        self.update_events_table()
        self.table.selectRow(row + 1)

    def clear_all_events(self):
        if len(self.current_script.events) == 0:
            return
        reply = QMessageBox.question(self, "確認", "確定要清空目前腳本中的所有事件嗎？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.current_script.events.clear()
            self.update_events_table()

    # --- 檔案管理功能 ---
    def new_script(self):
        self.current_script = MacroScript(name="新腳本")
        self.current_file_path = None
        self.lbl_script_name.setText("目前腳本：未儲存 (新腳本)")
        self.update_events_table()

    def open_script(self):
        path, _ = QFileDialog.getOpenFileName(self, "開啟巨集腳本檔案", self.script_mgr.scripts_dir, "JSON 巨集腳本 (*.json)")
        if path:
            try:
                self.current_script = self.script_mgr.load_script(path)
                self.current_file_path = path
                self.lbl_script_name.setText(f"目前腳本：{os.path.basename(path)}")
                self.update_events_table()

                # 反向更新播放設定至 UI
                st = self.current_script.settings
                self.spn_extra_delay.setValue(st.extra_delay_ms)
                self.spn_fixed_interval.setValue(st.fixed_interval_ms)
                self.spn_loops.setValue(st.loops)
                self.spn_loop_interval.setValue(st.loop_interval_sec)

                QMessageBox.information(self, "成功", f"已成功載入腳本: {self.current_script.name}")
            except Exception as e:
                QMessageBox.critical(self, "錯誤", f"腳本載入失敗: {e}")

    def save_script(self):
        if self.current_file_path:
            self.script_mgr.save_script(self.current_script, self.current_file_path)
            QMessageBox.information(self, "成功", "腳本已成功儲存！")
        else:
            self.save_script_as()

    def save_script_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "另存新巨集腳本", self.script_mgr.scripts_dir, "JSON 巨集腳本 (*.json)")
        if path:
            if not path.endswith(".json"):
                path += ".json"
            self.current_script.name = os.path.basename(path).replace(".json", "")
            self.current_file_path = path
            self.script_mgr.save_script(self.current_script, path)
            self.lbl_script_name.setText(f"目前腳本：{os.path.basename(path)}")
            QMessageBox.information(self, "成功", f"腳本已成功另存至:\n{path}")

    # --- 系統設定與關閉 ---
    def open_settings(self):
        dlg = SettingsWindow(self.sm, self)
        if dlg.exec():
            self.reload_hotkeys()

    @Slot()
    def show_normal_and_raise(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def closeEvent(self, event):
        if self.sm.get("minimize_to_tray", True):
            self.hide()
            self.tray_icon.showMessage(
                "Windows 巨集錄製器",
                "應用程式已縮小至右下角系統工作列，可隨時點擊或按快捷鍵執行巨集。",
                MacroSystemTray.MessageIcon.Information,
                2000
            )
            event.ignore()
        else:
            self.close_application()

    def close_application(self):
        self.hotkey_mgr.stop_listening()
        if self.player_thread and self.player_thread.isRunning():
            self.player_thread.stop()
            self.player_thread.wait()
        self.overlay.close()
        QApplication.quit()