"""
自訂快捷鍵輸入元件
使用者按下按鍵後自動偵測並顯示，支援複合按鍵（如 Ctrl+Shift+F1、X+C 等）
"""
from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent


# 修飾鍵對照表（Qt modifier → 顯示字串）
_MODIFIER_MAP = {
    Qt.KeyboardModifier.ControlModifier: "CTRL",
    Qt.KeyboardModifier.ShiftModifier:   "SHIFT",
    Qt.KeyboardModifier.AltModifier:     "ALT",
    Qt.KeyboardModifier.MetaModifier:    "WIN",
}

# 特殊鍵對照表（Qt.Key → 顯示字串）
_SPECIAL_KEY_MAP = {
    Qt.Key.Key_Escape:    "ESC",
    Qt.Key.Key_Return:    "ENTER",
    Qt.Key.Key_Enter:     "ENTER",
    Qt.Key.Key_Tab:       "TAB",
    Qt.Key.Key_Backspace: "BACKSPACE",
    Qt.Key.Key_Delete:    "DELETE",
    Qt.Key.Key_Insert:    "INSERT",
    Qt.Key.Key_Home:      "HOME",
    Qt.Key.Key_End:       "END",
    Qt.Key.Key_PageUp:    "PAGEUP",
    Qt.Key.Key_PageDown:  "PAGEDOWN",
    Qt.Key.Key_Up:        "UP",
    Qt.Key.Key_Down:      "DOWN",
    Qt.Key.Key_Left:      "LEFT",
    Qt.Key.Key_Right:     "RIGHT",
    Qt.Key.Key_Space:     "SPACE",
    Qt.Key.Key_CapsLock:  "CAPSLOCK",
    Qt.Key.Key_NumLock:   "NUMLOCK",
    Qt.Key.Key_ScrollLock:"SCROLLLOCK",
    Qt.Key.Key_Print:     "PRINTSCREEN",
    Qt.Key.Key_Pause:     "PAUSE",
    Qt.Key.Key_F1:  "F1",  Qt.Key.Key_F2:  "F2",  Qt.Key.Key_F3:  "F3",
    Qt.Key.Key_F4:  "F4",  Qt.Key.Key_F5:  "F5",  Qt.Key.Key_F6:  "F6",
    Qt.Key.Key_F7:  "F7",  Qt.Key.Key_F8:  "F8",  Qt.Key.Key_F9:  "F9",
    Qt.Key.Key_F10: "F10", Qt.Key.Key_F11: "F11", Qt.Key.Key_F12: "F12",
    Qt.Key.Key_F13: "F13", Qt.Key.Key_F14: "F14", Qt.Key.Key_F15: "F15",
    Qt.Key.Key_F16: "F16", Qt.Key.Key_F17: "F17", Qt.Key.Key_F18: "F18",
    Qt.Key.Key_F19: "F19", Qt.Key.Key_F20: "F20", Qt.Key.Key_F21: "F21",
    Qt.Key.Key_F22: "F22", Qt.Key.Key_F23: "F23", Qt.Key.Key_F24: "F24",
}

# 單獨按下時應忽略的「純修飾鍵」（不作為主鍵）
_MODIFIER_KEYS = {
    Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt,
    Qt.Key.Key_Meta, Qt.Key.Key_Super_L, Qt.Key.Key_Super_R,
}


class HotkeyInputWidget(QPushButton):
    """
    讓使用者直接按下按鍵（或組合鍵）來設定快捷鍵的輸入元件。

    使用方式：
        widget = HotkeyInputWidget("F6")
        current = widget.hotkey()   # 取得目前設定的字串，如 "CTRL+F6"
    """

    def __init__(self, initial_hotkey: str = "", parent=None):
        super().__init__(parent)
        self._hotkey = initial_hotkey.strip().upper()
        self._waiting = False           # 是否正在等待使用者按鍵
        self._pressed_keys: set = set() # 記錄目前按住的一般按鍵（非修飾鍵）

        self.setMinimumWidth(150)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCheckable(False)
        self.clicked.connect(self._start_capture)
        self._refresh_display()

    # ── 公開介面 ───────────────────────────────────────────────
    def hotkey(self) -> str:
        """回傳目前設定的快捷鍵字串（大寫，以 + 分隔）"""
        return self._hotkey

    def set_hotkey(self, hotkey: str):
        """程式化設定快捷鍵"""
        self._hotkey = hotkey.strip().upper()
        self._refresh_display()

    # ── 內部邏輯 ───────────────────────────────────────────────
    def _start_capture(self):
        """進入等待按鍵模式"""
        self._waiting = True
        self._pressed_keys.clear()
        self.setText("⌨  請按下按鍵組合...")
        self.setStyleSheet("background-color: #fffbe6; color: #ad6800; border: 2px solid #ffc53d; padding: 4px;")
        self.grabKeyboard()     # 捕獲鍵盤事件

    def _finish_capture(self, hotkey_str: str):
        """完成設定，離開等待模式"""
        self._waiting = False
        self.releaseKeyboard()
        if hotkey_str:
            self._hotkey = hotkey_str
        self._refresh_display()

    def _cancel_capture(self):
        """取消設定，恢復原有值"""
        self._waiting = False
        self.releaseKeyboard()
        self._refresh_display()

    def _refresh_display(self):
        """更新按鈕文字與樣式"""
        if self._hotkey:
            self.setText(f"🔑  {self._hotkey}")
        else:
            self.setText("點擊設定快捷鍵...")
        self.setStyleSheet("")

    # ── Qt 事件覆寫 ────────────────────────────────────────────
    def keyPressEvent(self, event: QKeyEvent):
        if not self._waiting:
            return super().keyPressEvent(event)

        key = Qt.Key(event.key())

        # ESC → 取消設定
        if key == Qt.Key.Key_Escape:
            self._cancel_capture()
            return

        # 忽略純修飾鍵（等待主鍵）
        if key in _MODIFIER_KEYS:
            return

        # ── 組合此次按鍵字串 ──
        parts = []

        # 1. 修飾鍵（按照 Ctrl > Shift > Alt > Win 順序）
        mods = event.modifiers()
        for mod, label in _MODIFIER_MAP.items():
            if mods & mod:
                parts.append(label)

        # 2. 主鍵：先查特殊對照表，再嘗試文字，最後 fallback 到 Qt 名稱
        if key in _SPECIAL_KEY_MAP:
            parts.append(_SPECIAL_KEY_MAP[key])
        else:
            text = event.text().upper()
            if text and text.isprintable():
                parts.append(text)
            else:
                key_name = event.key()
                fallback = Qt.Key(key_name).name if hasattr(Qt.Key(key_name), "name") else str(key_name)
                # 嘗試從列舉名稱取得（如 Key_A → A）
                try:
                    name = Qt.Key(key_name).name.replace("Key_", "")
                    if name:
                        parts.append(name.upper())
                except Exception:
                    parts.append(str(key_name))

        hotkey_str = "+".join(parts)
        self._pressed_keys.add(hotkey_str)
        self._finish_capture(hotkey_str)

    def keyReleaseEvent(self, event: QKeyEvent):
        if self._waiting:
            return  # 在等待狀態中不處理 release
        super().keyReleaseEvent(event)

    def focusOutEvent(self, event):
        """失去焦點時自動取消設定"""
        if self._waiting:
            self._cancel_capture()
        super().focusOutEvent(event)
