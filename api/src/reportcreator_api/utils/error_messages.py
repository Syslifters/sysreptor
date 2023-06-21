import dataclasses
import enum
from typing import Optional, Union


class MessageLevel(enum.Enum):
    ERROR = 'error'
    WARNING = 'warning'
    INFO = 'info'
    DEBUG = 'debug'


class MessageLocationType(enum.Enum):
    FINDING = 'finding'
    PROJECT = 'project'
    SECTION = 'section'
    DESIGN = 'design'
    OTHER = 'other'


def format_path(path: Union[None, str, tuple[str], list[str]]):
    path_str = path
    if isinstance(path, (tuple, list)):
        path_str = ''
        for p in path:
            if path_str and p and p[0] != '[':
                path_str += '.'
            path_str += p
    return path_str


@dataclasses.dataclass
class MessageLocationInfo:
    type: MessageLocationType
    id: Optional[str] = None
    name: Optional[str] = None
    path: Optional[str] = None

    def sub_path(self, sub_path: str):
        path = self.path or ''
        if sub_path.startswith('[') or not path:
            path += sub_path
        else:
            path += '.' + sub_path
        return MessageLocationInfo(**(dataclasses.asdict(self) | {'path': path}))

    def for_path(self, path: Union[None, str, tuple[str], list[str]]):
        return MessageLocationInfo(**(dataclasses.asdict(self)  |{'path': format_path(path)}))
    
    def to_dict(self):
        return dataclasses.asdict(self) | {
            'type': self.type.value,
        }


@dataclasses.dataclass
class ErrorMessage:
    level: MessageLevel
    message: str
    details: Optional[str] = None
    location: Optional[MessageLocationInfo] = None

    def to_dict(self):
        return dataclasses.asdict(self) | {
            'level': self.level.value,
            'location': self.location.to_dict() if self.location else None,
        }
    
    @classmethod
    def from_dict(cls, data):
        location = data.get('location')
        return cls(**data | {
            'level': MessageLevel(data.get('level')),
            'location': MessageLocationInfo(**location | {'type': MessageLocationType(location.get('type'))}) if location else None,
        })


