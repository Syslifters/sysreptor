"""
Helpers for embedding SysReptor images inline in Jira ADF documents.

The frontend converts markdown images referencing SysReptor uploads (``/images/name/<name>``)
to ADF placeholder nodes::

    {"type": "mediaSingle", "attrs": {"layout": "center"}, "content": [
        {"type": "media", "attrs": {"type": "external", "url": "/images/name/<name>"}}
    ]}

The backend uploads the image as Jira attachment, resolves the Media Services file ID of the
attachment and replaces the placeholder with ``{"type": "file", "id": <media-id>, "collection": ""}``.
This is the same structure Jira creates when an image is pasted into the description editor.
"""
import copy
import io
import re
from urllib.parse import urlsplit

from PIL import Image

SYSREPTOR_IMAGE_PREFIX = '/images/name/'
MEDIA_ID_PATTERN = re.compile(r'/file/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})(?:/|$|\?)')


def image_name_from_url(url: str | None) -> str | None:
    if not url or not url.startswith(SYSREPTOR_IMAGE_PREFIX):
        return None
    name = urlsplit(url).path[len(SYSREPTOR_IMAGE_PREFIX):]
    # Jira rejects attachment filenames containing these characters.
    name = ''.join(c for c in name if c not in ['\\', '/', '"', '%', ':', '$', '?', '*'])
    return name or None


def _placeholder_name(node: dict) -> str | None:
    if not isinstance(node, dict) or node.get('type') != 'media':
        return None
    attrs = node.get('attrs') or {}
    if attrs.get('type') != 'external':
        return None
    return image_name_from_url(attrs.get('url'))


def _walk(node):
    if isinstance(node, dict):
        yield node
        for child in node.get('content') or []:
            yield from _walk(child)


def get_referenced_image_names(adf: dict) -> list[str]:
    """Image names referenced by placeholders, in document order, without duplicates."""
    names = (_placeholder_name(n) for n in _walk(adf))
    return list(dict.fromkeys(n for n in names if n))


def _transform_media_singles(adf: dict, fn) -> dict:
    """
    Return a deep copy of ``adf`` where every mediaSingle node containing a placeholder
    is replaced by ``fn(media_single_node, image_name)`` (a list of nodes).
    """
    adf = copy.deepcopy(adf)

    def visit(node):
        if not isinstance(node, dict) or not isinstance(node.get('content'), list):
            return
        new_content = []
        for child in node['content']:
            if isinstance(child, dict) and child.get('type') == 'mediaSingle':
                media = next(iter(child.get('content') or []), None)
                name = _placeholder_name(media)
                if name:
                    new_content.extend(fn(child, name))
                    continue
            visit(child)
            new_content.append(child)
        node['content'] = new_content

    visit(adf)
    return adf


def strip_image_placeholders(adf: dict) -> dict:
    """
    Remove placeholders (used for the initial issue creation, before attachments exist).
    An empty paragraph is kept in place, because e.g. listItem and tableCell must not be empty.
    """
    return _transform_media_singles(adf, lambda node, name: [{'type': 'paragraph', 'content': []}])


def replace_image_placeholders(adf: dict, media_attrs_by_name: dict[str, dict]) -> dict:
    """
    Replace placeholders with resolved media attrs.
    Unresolvable images fall back to a text reference instead of breaking the issue.
    """
    def replace(node, name):
        attrs = media_attrs_by_name.get(name)
        if not attrs:
            return [{'type': 'paragraph', 'content': [{'type': 'text', 'text': f'[image: {name}]'}]}]
        media = node['content'][0]
        alt = (media.get('attrs') or {}).get('alt')
        media['attrs'] = {**attrs, **({'alt': alt} if alt else {})}
        return [node]
    return _transform_media_singles(adf, replace)


def extract_media_id(url: str | None) -> str | None:
    """Extract the Media Services file ID from an attachment content redirect URL
    (e.g. https://api.media.atlassian.com/file/<uuid>/binary?token=...)."""
    if not url:
        return None
    m = MEDIA_ID_PATTERN.search(url)
    return m.group(1).lower() if m else None


def get_image_size(data: bytes | None) -> tuple[int, int] | None:
    """Pixel size of an image (as displayed, respecting EXIF orientation). Reads only the header."""
    if not data:
        return None
    try:
        with Image.open(io.BytesIO(data)) as img:
            width, height = img.size
            if img.getexif().get(0x0112) in (5, 6, 7, 8):  # rotated by 90/270 degrees
                width, height = height, width
    except (OSError, ValueError, SyntaxError, Image.DecompressionBombError):
        return None
    if width <= 0 or height <= 0:
        return None
    return width, height
