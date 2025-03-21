import dataclasses
import enum


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


def format_path(path: None | str | tuple[str] | list[str]):
    path_str = path
    if isinstance(path, tuple|list):
        path_str = '.'.join(path)
    if path_str:
        path_str = path_str.replace('.[', '[')
    return path_str


@dataclasses.dataclass(eq=True, frozen=True)
class MessageLocationInfo:
    type: MessageLocationType
    id: str | None = None
    name: str | None = None
    path: str | None = None

    def sub_path(self, sub_path: str):
        path = self.path or ''
        if sub_path.startswith('[') or not path:
            path += sub_path
        else:
            path += '.' + sub_path
        return MessageLocationInfo(**(dataclasses.asdict(self) | {'path': path}))

    def for_path(self, path: None | str | tuple[str] | list[str]):
        return MessageLocationInfo(**(dataclasses.asdict(self)  |{'path': format_path(path)}))

    def to_dict(self):
        return dataclasses.asdict(self) | {
            'type': self.type.value,
        }


@dataclasses.dataclass(eq=True, frozen=True)
class ErrorMessage:
    level: MessageLevel
    message: str
    details: str | None = None
    location: MessageLocationInfo | None = None

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


