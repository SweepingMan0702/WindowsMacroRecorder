from dataclasses import dataclass, field
from typing import List, Dict, Any
import time
from core.events import MacroEvent

@dataclass
class PlaybackSettings:
    speed: float = 1.0
    loops: int = 1  # 0 代表無限循環
    extra_delay: int = 0  # 毫秒
    fixed_interval: int = -1  # 毫秒, -1 代表使用原記錄延遲
    loop_interval: float = 0.0  # 秒

    @property
    def extra_delay_ms(self) -> int:
        return self.extra_delay

    @extra_delay_ms.setter
    def extra_delay_ms(self, val: int):
        self.extra_delay = val

    @property
    def fixed_interval_ms(self) -> int:
        return self.fixed_interval

    @fixed_interval_ms.setter
    def fixed_interval_ms(self, val: int):
        self.fixed_interval = val

    @property
    def loop_interval_sec(self) -> float:
        return self.loop_interval

    @loop_interval_sec.setter
    def loop_interval_sec(self, val: float):
        self.loop_interval = val

    def to_dict(self) -> Dict[str, Any]:
        return {
            "speed": self.speed,
            "loops": self.loops,
            "extra_delay": self.extra_delay,
            "fixed_interval": self.fixed_interval,
            "loop_interval": self.loop_interval,
            "extra_delay_ms": self.extra_delay,
            "fixed_interval_ms": self.fixed_interval,
            "loop_interval_sec": self.loop_interval
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlaybackSettings':
        if not data:
            return cls()
        speed = data.get("speed", 1.0)
        loops = data.get("loops", 1)
        extra_delay = data.get("extra_delay", data.get("extra_delay_ms", 0))
        fixed_interval = data.get("fixed_interval", data.get("fixed_interval_ms", -1))
        loop_interval = data.get("loop_interval", data.get("loop_interval_sec", 0.0))
        return cls(
            speed=speed,
            loops=loops,
            extra_delay=extra_delay,
            fixed_interval=fixed_interval,
            loop_interval=loop_interval
        )

@dataclass
class MacroScript:
    name: str = "新腳本"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    events: List[MacroEvent] = field(default_factory=list)
    settings: PlaybackSettings = field(default_factory=PlaybackSettings)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "events": [e.to_dict() for e in self.events],
            "settings": self.settings.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MacroScript':
        events = [MacroEvent.from_dict(e) for e in data.get("events", [])]
        settings = PlaybackSettings.from_dict(data.get("settings", {}))
        return cls(
            name=data.get("name", "未命名腳本"),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            events=events,
            settings=settings
        )