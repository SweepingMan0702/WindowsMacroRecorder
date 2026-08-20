from PySide6.QtCore import QObject, Signal
from pynput import keyboard
from utils.logger import logger

def _normalize_hotkey(key_str: str) -> str:
    if not key_str:
        return ""
    parts = [p.strip() for p in key_str.split('+')]
    formatted = []
    for p in parts:
        lower = p.lower()
        if lower.startswith('<') and lower.endswith('>'):
            formatted.append(lower)
        elif len(lower) > 1:
            formatted.append(f'<{lower}>')
        else:
            formatted.append(lower)
    return '+'.join(formatted)

class GlobalHotkeyManager(QObject):
    record_toggle_triggered = Signal()
    play_toggle_triggered = Signal()
    pause_toggle_triggered = Signal()
    stop_triggered = Signal()
    emergency_stop_triggered = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._listener = None
        self._hotkey_mapping = {}

    def update_hotkeys(self, record_key: str = "F6", play_key: str = "F7", pause_key: str = "F8", stop_key: str = "F9", emergency_key: str = "ESC"):
        self.stop_listening()

        mapping = {}
        if record_key:
            mapping[_normalize_hotkey(record_key)] = self.record_toggle_triggered.emit
        if play_key:
            mapping[_normalize_hotkey(play_key)] = self.play_toggle_triggered.emit
        if pause_key:
            mapping[_normalize_hotkey(pause_key)] = self.pause_toggle_triggered.emit
        if stop_key:
            mapping[_normalize_hotkey(stop_key)] = self.stop_triggered.emit
        if emergency_key:
            mapping[_normalize_hotkey(emergency_key)] = self.emergency_stop_triggered.emit

        self._hotkey_mapping = mapping
        self.start_listening()

    def start_listening(self):
        self.stop_listening()
        if not self._hotkey_mapping:
            return
        try:
            self._listener = keyboard.GlobalHotKeys(self._hotkey_mapping)
            self._listener.start()
            logger.info("GlobalHotkeyManager: 全域熱鍵已成功監聽")
        except Exception as e:
            logger.error(f"GlobalHotkeyManager 綁定熱鍵失敗: {e}")

    def stop_listening(self):
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None

    def start(self):
        self.start_listening()

    def stop(self):
        self.stop_listening()