import time
from typing import List, Optional, Set
from pynput import mouse, keyboard
from core.events import MacroEvent, EventType
from utils.logger import logger

VK_MAP = {
    8: 'backspace', 9: 'tab', 13: 'enter', 27: 'esc', 32: 'space',
    33: 'page_up', 34: 'page_down', 35: 'end', 36: 'home',
    37: 'left', 38: 'up', 39: 'right', 40: 'down',
    45: 'insert', 46: 'delete',
    186: ';', 187: '=', 188: ',', 189: '-', 190: '.', 191: '/', 192: '`',
    219: '[', 220: '\\', 221: ']', 222: "'"
}

class MacroRecorder:
    def __init__(self):
        self.events: List[MacroEvent] = []
        self.is_recording = False
        self.is_paused = False
        
        self.record_mouse_move = True
        self.record_mouse_click = True
        self.record_mouse_scroll = True
        self.record_keyboard = True
        
        self.ignored_hotkeys: Set[str] = set()
        self._currently_pressed_keys: Set[str] = set()

        self._start_time = 0.0
        self._pause_start_time = 0.0
        self._paused_duration = 0.0
        self._last_event_time = 0.0
        
        self._mouse_listener = None
        self._keyboard_listener = None

    def set_ignored_hotkeys(self, hotkeys: List[str]):
        ignored = set()
        for hk in hotkeys:
            if not hk:
                continue
            parts = [p.strip().lower() for p in hk.split('+')]
            for p in parts:
                if p.startswith('<') and p.endswith('>'):
                    p = p[1:-1]
                ignored.add(p)
        self.ignored_hotkeys = ignored
        logger.info(f"MacroRecorder: 成功設定需過濾的程式快捷鍵: {self.ignored_hotkeys}")

    def start(self):
        if self.is_recording and self.is_paused:
            self.resume()
            return

        self.events.clear()
        self._currently_pressed_keys.clear()
        self.is_recording = True
        self.is_paused = False
        self._start_time = time.perf_counter()
        self._pause_start_time = 0.0
        self._paused_duration = 0.0
        self._last_event_time = self._start_time

        self._mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll
        )
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self._mouse_listener.start()
        self._keyboard_listener.start()
        logger.info("MacroRecorder: 開始錄製操作")

    def pause(self):
        if self.is_recording and not self.is_paused:
            self.is_paused = True
            self._pause_start_time = time.perf_counter()
            self._currently_pressed_keys.clear()
            logger.info("MacroRecorder: 暫停錄製操作")

    def resume(self):
        if self.is_recording and self.is_paused:
            now = time.perf_counter()
            self._paused_duration += (now - self._pause_start_time)
            self._last_event_time = now
            self.is_paused = False
            self._currently_pressed_keys.clear()
            logger.info("MacroRecorder: 恢復錄製操作")

    def stop(self) -> List[MacroEvent]:
        self.is_recording = False
        self.is_paused = False
        self._currently_pressed_keys.clear()
        if self._mouse_listener:
            try:
                self._mouse_listener.stop()
            except Exception:
                pass
            self._mouse_listener = None
        if self._keyboard_listener:
            try:
                self._keyboard_listener.stop()
            except Exception:
                pass
            self._keyboard_listener = None
        logger.info(f"MacroRecorder: 停止錄製，共錄製 {len(self.events)} 個事件")
        return self.events

    def get_elapsed_time(self) -> float:
        if not self.is_recording:
            return 0.0
        now = time.perf_counter()
        if self.is_paused:
            elapsed = self._pause_start_time - self._start_time - self._paused_duration
        else:
            elapsed = now - self._start_time - self._paused_duration
        return max(0.0, round(elapsed, 2))

    def _get_delay(self) -> float:
        now = time.perf_counter()
        delay = now - self._last_event_time
        self._last_event_time = now
        return max(0.001, round(delay, 4))

    def _on_mouse_move(self, x: int, y: int):
        if not self.is_recording or self.is_paused or not self.record_mouse_move:
            return
        evt = MacroEvent(type=EventType.MOUSE_MOVE, x=x, y=y, delay=self._get_delay())
        self.events.append(evt)

    def _on_mouse_click(self, x: int, y: int, button: mouse.Button, pressed: bool):
        if not self.is_recording or self.is_paused or not self.record_mouse_click:
            return
        evt_type = EventType.MOUSE_PRESS if pressed else EventType.MOUSE_RELEASE
        evt = MacroEvent(type=evt_type, x=x, y=y, button=button.name, delay=self._get_delay())
        self.events.append(evt)

    def _on_mouse_scroll(self, x: int, y: int, dx: int, dy: int):
        if not self.is_recording or self.is_paused or not self.record_mouse_scroll:
            return
        evt = MacroEvent(type=EventType.MOUSE_SCROLL, x=x, y=y, dx=dx, dy=dy, delay=self._get_delay())
        self.events.append(evt)

    def _on_key_press(self, key):
        if not self.is_recording or self.is_paused or not self.record_keyboard:
            return
        key_str = self._key_to_string(key)
        if self._is_ignored_key(key_str):
            return
        
        # 避免作業系統 auto-repeat 重複洗板，但完整保留多鍵同時按壓 (如 A+W, W+D 等遊戲/巨集多鍵組合)
        if key_str in self._currently_pressed_keys:
            return
        self._currently_pressed_keys.add(key_str)

        evt = MacroEvent(type=EventType.KEY_PRESS, key=key_str, delay=self._get_delay())
        self.events.append(evt)

    def _on_key_release(self, key):
        if not self.is_recording or self.is_paused or not self.record_keyboard:
            return
        key_str = self._key_to_string(key)
        if self._is_ignored_key(key_str):
            return
        
        self._currently_pressed_keys.discard(key_str)

        evt = MacroEvent(type=EventType.KEY_RELEASE, key=key_str, delay=self._get_delay())
        self.events.append(evt)

    def _is_ignored_key(self, key_str: str) -> bool:
        if not key_str or not self.ignored_hotkeys:
            return False
        k_lower = key_str.lower()
        if k_lower in self.ignored_hotkeys:
            return True
        if k_lower.startswith('f') and k_lower in self.ignored_hotkeys:
            return True
        return False

    def _key_to_string(self, key) -> str:
        if isinstance(key, keyboard.Key):
            return key.name
        
        vk = getattr(key, 'vk', None)
        char = getattr(key, 'char', None)
        
        if vk is not None:
            if 65 <= vk <= 90:
                return chr(vk).lower()
            if 48 <= vk <= 57:
                return chr(vk)
            if 96 <= vk <= 105:
                return str(vk - 96)
            if 112 <= vk <= 123:
                return f"f{vk - 111}"
            if vk in VK_MAP:
                return VK_MAP[vk]

        if char is not None:
            if len(char) == 1 and 1 <= ord(char) <= 26:
                return chr(ord(char) + 96)
            return char

        if hasattr(key, 'name') and key.name is not None:
            return key.name

        return str(key)