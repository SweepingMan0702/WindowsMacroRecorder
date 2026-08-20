from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, Dict, Any

class EventType(str, Enum):
    MOUSE_MOVE = "mouse_move"
    MOUSE_PRESS = "mouse_press"
    MOUSE_RELEASE = "mouse_release"
    MOUSE_SCROLL = "mouse_scroll"
    KEY_PRESS = "key_press"
    KEY_RELEASE = "key_release"

@dataclass
class MacroEvent:
    type: EventType = EventType.MOUSE_MOVE
    delay: float = 0.0
    x: int = 0
    y: int = 0
    button: Optional[str] = None
    key: Optional[str] = None
    dx: int = 0
    dy: int = 0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['type'] = self.type.value if isinstance(self.type, Enum) else str(self.type)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MacroEvent':
        data_copy = data.copy()
        data_copy['type'] = EventType(data_copy['type'])
        return cls(**data_copy)