import contextlib
import dataclasses
import re
import time
from base64 import b64decode, b64encode
from io import BytesIO
from pathlib import Path
from typing import Any

from weasyprint.urls import URLFetchingError

from .error_messages import ErrorMessage, MessageLevel, MessageLocationInfo, MessageLocationType

# Base URL prefix for PDF rendering. Is never actually called
FAKE_BASE_URL = 'https://pdf.sysreptor.com'


@dataclasses.dataclass()
class RenderStageResult:
    pdf: bytes | None = None
    messages: list[ErrorMessage] = dataclasses.field(default_factory=list)
    timings: dict[str, float] = dataclasses.field(default_factory=dict)
    other: dict[str, Any] = dataclasses.field(default_factory=dict)

    def to_dict(self, include_other=False):
        res = dataclasses.asdict(self) | {
            'pdf': b64encode(self.pdf).decode() if self.pdf else None,
            'messages': [m.to_dict() for m in self.messages],
        }
        if not include_other:
            del res['other']
        return res

    @classmethod
    def from_dict(cls, data):
        return cls(
            pdf=b64decode(data['pdf']) if data.get('pdf') is not None else None,
            messages=[ErrorMessage.from_dict(m) for m in data.get('messages', [])],
            timings=data.get('timings', {}),
            other=data.get('other', {}),
        )

    def __or__(self, value: 'RenderStageResult') -> 'RenderStageResult':
        return RenderStageResult(
            pdf=value.pdf,
            messages=list(set(self.messages + value.messages)),
            timings=self.timings | {k: self.timings.get(k, 0) + v for k, v in value.timings.items()},
            other=self.other | value.other,
        )

    @contextlib.contextmanager
    def add_timing(self, name: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            self.timings[name] = self.timings.get(name, 0) + elapsed


def get_location_info(content: str, objs: list[dict], type: MessageLocationType, get_name=None) -> MessageLocationInfo | None:
    def check_field(val, path, **kwargs):
        if isinstance(val, dict):
            return check_obj(val, path, **kwargs)
        elif isinstance(val, list):
            for idx, item in enumerate(val):
                if res := check_field(val=item, path=path + [f'[{idx}]'], **kwargs):
                    return res
        elif isinstance(val, str):
            if content in val:
                return MessageLocationInfo(type=type, **kwargs).for_path(path)

    def check_obj(obj, path, **kwargs):
        for k, v in obj.items():
            if res := check_field(val=v, path=path + [k], **kwargs):
                return res

    for o in objs:
        if res := check_field(val=o, path=[], id=o.get('id'), name=get_name(o) if get_name else None):
            return res


def get_location(content, data):
    return get_location_info(content=content, objs=data.get('findings', []), type=MessageLocationType.FINDING, get_name=lambda f: f.get('title')) or \
           get_location_info(content=content, objs=data.get('sections', {}).values(), type=MessageLocationType.SECTION, get_name=lambda s: s.get('label')) or \
           None


def request_handler(url, resources: dict[str, str], messages: list[ErrorMessage], data: dict) -> dict:
    if url.startswith(FAKE_BASE_URL):
        url = url[len(FAKE_BASE_URL):]

    # allow loading from the resource list
    if url in resources:
        return {
            'filename': url.split('/')[-1],
            'file_obj': BytesIO(b64decode(resources[url])),
        }
    elif (m := re.fullmatch(r'^/assets/global/([a-z0-9-_.]+)$', url)) and (global_asset := Path(__file__).parent / 'global_assets' / m.group(1)) and global_asset.exists():
        return {
            'filename': global_asset.name,
            'file_obj': global_asset.open('rb'),
        }
    elif url.startswith('/'):
        messages.append(ErrorMessage(
            level=MessageLevel.WARNING,
            message='Resource not found',
            details=f'Could not find resource for URL "{url}". Check if the URL is correct and the resource exists on the server.',
            location=get_location(content=url, data=data),
        ))
        raise URLFetchingError('Resource not found')
    else:
        # block all external requests
        messages.append(ErrorMessage(
            level=MessageLevel.WARNING,
            message='Blocked request to external URL',
            details=f'Block request to URL "{url}". Requests to external systems are forbidden for security reasons.\nUpload this resource as assset and include it via its asset URL.',
        ))
        raise URLFetchingError('External requests are not allowed')
