import os
import json
from typing import Dict, Any, Optional
from utils.logger import logger

class SettingsManager:
    def __init__(self, settings_file: Optional[str] = None):
        self.settings_file = settings_file or os.path.join(os.getcwd(), "settings.json")
        self.defaults = {
            "record_mouse_move": True,
            "record_mouse_click": True,
            "record_mouse_scroll": True,
            "record_keyboard": True,
            "hotkey_record": "F6",
            "hotkey_play": "F7",
            "hotkey_pause": "F8",
            "hotkey_stop": "F9",
            "hotkey_emergency": "ESC",
            "show_overlay": True,
            "overlay_position": "右上角",
            "minimize_to_tray": True,
            "default_speed": 1.0,
            "default_loops": 1,
            "default_delay_ms": 0
        }
        self.settings = self.load_settings()

    def load_settings(self) -> Dict[str, Any]:
        if not os.path.exists(self.settings_file):
            return self.defaults.copy()
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged = self.defaults.copy()
                merged.update(data)
                return merged
        except Exception as e:
            logger.error(f"讀取設定檔失敗，使用預設值: {e}")
            return self.defaults.copy()

    def save_settings(self) -> None:
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            logger.info("偏好設定已成功儲存")
        except Exception as e:
            logger.error(f"儲存設定檔失敗: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.settings[key] = value
        self.save_settings()