import time
from typing import Optional
from PySide6.QtCore import QThread, Signal
from pynput import mouse, keyboard
from core.events import MacroEvent, EventType
from models.script import MacroScript, PlaybackSettings
from utils.windows import release_all_keys
from utils.logger import logger

class MacroPlayerThread(QThread):
    progress_updated = Signal(int, int, int, int) # (current_index, total_events, current_loop, total_loops)
    status_changed = Signal(str)
    finished_playback = Signal()
    error_occurred = Signal(str)

    def __init__(self, script: MacroScript, settings: Optional[PlaybackSettings] = None, parent=None):
        super().__init__(parent)
        self.script = script
        self.settings = settings or script.settings or PlaybackSettings()
        self._is_running = False
        self._is_paused = False
        self._mouse_controller = mouse.Controller()
        self._keyboard_controller = keyboard.Controller()
        self._pressed_mouse_buttons = set()
        self._pressed_keys = set()

    def run(self):
        self._is_running = True
        self._is_paused = False
        self._pressed_mouse_buttons.clear()
        self._pressed_keys.clear()
        events = self.script.events
        total_events = len(events)
        if total_events == 0:
            self.finished_playback.emit()
            return

        speed = max(0.01, self.settings.speed)
        total_loops = self.settings.loops
        loop_count = 0

        logger.info(f"MacroPlayer: 開始播放，共 {total_events} 個事件，倍率 {speed}x，目標循環 {total_loops}")

        try:
            while self._is_running:
                loop_count += 1
                for idx, event in enumerate(events):
                    if not self._is_running:
                        break
                    while self._is_paused and self._is_running:
                        self.msleep(50)

                    self.progress_updated.emit(idx + 1, total_events, loop_count, total_loops)
                    self._execute_event(event, speed)

                if total_loops > 0 and loop_count >= total_loops:
                    break

                if self.settings.loop_interval > 0 and self._is_running:
                    time.sleep(self.settings.loop_interval)

        except Exception as e:
            logger.error(f"MacroPlayer 執行時出錯: {e}")
            self.error_occurred.emit(str(e))
        finally:
            for btn in list(self._pressed_mouse_buttons):
                try:
                    self._mouse_controller.release(btn)
                except Exception:
                    pass
            self._pressed_mouse_buttons.clear()

            for k in list(self._pressed_keys):
                try:
                    self._keyboard_controller.release(k)
                except Exception:
                    pass
            self._pressed_keys.clear()

            release_all_keys(self._keyboard_controller, self._mouse_controller)
            self._is_running = False
            self.finished_playback.emit()

    def _execute_event(self, event: MacroEvent, speed: float):
        delay = event.delay / speed
        if self.settings.fixed_interval >= 0:
            delay = self.settings.fixed_interval / 1000.0
        delay += (self.settings.extra_delay / 1000.0)

        if delay > 0:
            time.sleep(max(0.001, delay))

        t = event.type
        if t == EventType.MOUSE_MOVE:
            self._mouse_controller.position = (event.x, event.y)
        elif t == EventType.MOUSE_PRESS:
            self._mouse_controller.position = (event.x, event.y)
            btn = self._parse_button(event.button)
            self._mouse_controller.press(btn)
            self._pressed_mouse_buttons.add(btn)
        elif t == EventType.MOUSE_RELEASE:
            self._mouse_controller.position = (event.x, event.y)
            btn = self._parse_button(event.button)
            self._mouse_controller.release(btn)
            self._pressed_mouse_buttons.discard(btn)
        elif t == EventType.MOUSE_SCROLL:
            self._mouse_controller.scroll(event.dx, event.dy)
        elif t == EventType.KEY_PRESS:
            if event.key:
                keys = [self._parse_key(k.strip()) for k in event.key.split('+')] if '+' in event.key else [self._parse_key(event.key)]
                for k in keys:
                    if k:
                        self._keyboard_controller.press(k)
                        self._pressed_keys.add(k)
        elif t == EventType.KEY_RELEASE:
            if event.key:
                keys = [self._parse_key(k.strip()) for k in event.key.split('+')] if '+' in event.key else [self._parse_key(event.key)]
                for k in reversed(keys):
                    if k:
                        self._keyboard_controller.release(k)
                        self._pressed_keys.discard(k)

    def _parse_button(self, button_str: Optional[str]) -> mouse.Button:
        if isinstance(button_str, mouse.Button):
            return button_str
        if isinstance(button_str, str) and hasattr(mouse.Button, button_str.lower()):
            return getattr(mouse.Button, button_str.lower())
        return mouse.Button.left

    def _parse_key(self, key_str: Optional[str]):
        if not key_str:
            return None
        k_lower = key_str.lower()
        if hasattr(keyboard.Key, k_lower):
            return getattr(keyboard.Key, k_lower)
        if hasattr(keyboard.Key, key_str):
            return getattr(keyboard.Key, key_str)
        if k_lower.endswith('_l') or k_lower.endswith('_r'):
            base_name = k_lower[:-2]
            if hasattr(keyboard.Key, base_name):
                return getattr(keyboard.Key, base_name)
        return key_str

    def pause(self):
        self._is_paused = True

    def resume(self):
        self._is_paused = False

    def toggle_pause(self):
        self._is_paused = not self._is_paused

    def stop(self):
        self._is_running = False

    def stop_playback(self):
        self.stop()