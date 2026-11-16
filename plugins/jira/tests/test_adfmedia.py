import io

from PIL import Image

from ..adfmedia import (
    extract_media_id,
    get_image_size,
    get_referenced_image_names,
    image_name_from_url,
    replace_image_placeholders,
    strip_image_placeholders,
)


def placeholder(url, alt=None):
    return {'type': 'mediaSingle', 'attrs': {'layout': 'center'}, 'content': [
        {'type': 'media', 'attrs': {'type': 'external', 'url': url, **({'alt': alt} if alt else {})}},
    ]}


def doc(*content):
    return {'version': 1, 'type': 'doc', 'content': list(content)}


def test_image_name_from_url():
    assert image_name_from_url('/images/name/img.png') == 'img.png'
    assert image_name_from_url('/images/name/my%20img.png') == 'my img.png'
    assert image_name_from_url('https://example.com/img.png') is None
    assert image_name_from_url('/images/name/') is None


def test_extract_media_id():
    url = 'https://api.media.atlassian.com/file/12345678-1234-1234-1234-123456789ABC/binary?token=abc'
    assert extract_media_id(url) == '12345678-1234-1234-1234-123456789abc'
    assert extract_media_id('https://example.com/other') is None
    assert extract_media_id(None) is None


def test_referenced_image_names():
    adf = doc(
        placeholder('/images/name/a.png'),
        placeholder('https://example.com/external.png'),
        {'type': 'bulletList', 'content': [{'type': 'listItem', 'content': [placeholder('/images/name/b.png')]}]},
        placeholder('/images/name/a.png'),
    )
    assert get_referenced_image_names(adf) == ['a.png', 'b.png']


def test_strip_keeps_valid_structure():
    adf = doc({'type': 'bulletList', 'content': [{'type': 'listItem', 'content': [placeholder('/images/name/a.png')]}]})
    stripped = strip_image_placeholders(adf)
    assert stripped['content'][0]['content'][0]['content'] == [{'type': 'paragraph', 'content': []}]
    # input is not modified
    assert adf['content'][0]['content'][0]['content'][0]['type'] == 'mediaSingle'


def test_replace_placeholders():
    adf = doc(placeholder('/images/name/a.png', alt='Caption'), placeholder('/images/name/missing.png'), placeholder('https://example.com/x.png'))
    res = replace_image_placeholders(adf, {'a.png': {'type': 'file', 'id': 'media-id', 'collection': ''}})
    assert res['content'][0]['content'][0]['attrs'] == {'type': 'file', 'id': 'media-id', 'collection': '', 'alt': 'Caption'}
    assert res['content'][1] == {'type': 'paragraph', 'content': [{'type': 'text', 'text': '[image: missing.png]'}]}
    assert res['content'][2] == placeholder('https://example.com/x.png')


def test_get_image_size():
    buf = io.BytesIO()
    Image.new('RGB', (1280, 720)).save(buf, format='PNG')
    assert get_image_size(buf.getvalue()) == (1280, 720)
    assert get_image_size(b'not an image') is None
    assert get_image_size(None) is None
