import io
import logging
import string
from pathlib import Path

from django.apps import apps
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile, File
from django.core.files.storage import storages
from django.core.validators import FileExtensionValidator
from django.db import models
from django.forms.fields import FileField, ImageField
from django.utils.translation import gettext_lazy as _
from PIL import Image, ImageOps, UnidentifiedImageError

from sysreptor.utils.configuration import configuration
from sysreptor.utils.logging import log_timing

log = logging.getLogger(__name__)

ALLOWED_IMAGE_FORMATS = ('JPEG', 'PNG', 'GIF', 'WEBP', 'TIFF', 'AVIF', 'BMP', 'DIB', 'ICO', 'PPM', 'JPEG2000')


def get_allowed_image_extensions():
    Image.init()
    return sorted({
        ext.lstrip('.').lower()
        for ext, fmt in Image.EXTENSION.items()
        if fmt in ALLOWED_IMAGE_FORMATS
    })


class RestrictedImageField(ImageField):
    """
    Django forms ImageField that only opens image formats in ALLOWED_IMAGE_FORMATS.

    Based on django.forms.fields.ImageField; keep in sync on Django upgrades.
    """

    default_validators = [FileExtensionValidator(allowed_extensions=get_allowed_image_extensions())]
    default_error_messages = {
        'invalid_image': _(
            'Upload a valid image. The file you uploaded was either not an '
            'image or a corrupted image.',
        ),
    }

    def to_python(self, data):
        f = FileField.to_python(self, data)
        if f is None:
            return None

        # We need to get a file object for Pillow. We might have a path or we
        # might have to read the data into memory.
        if hasattr(data, 'temporary_file_path'):
            file = data.temporary_file_path()
        else:
            if hasattr(data, 'read'):
                file = io.BytesIO(data.read())
            else:
                file = io.BytesIO(data['content'])

        try:
            # load() could spot a truncated JPEG, but it loads the entire
            # image in memory, which is a DoS vector. See #3848 and #18520.
            image = Image.open(file, formats=ALLOWED_IMAGE_FORMATS)
            # verify() must be called immediately after the constructor.
            image.verify()

            # Annotating so subclasses can reuse it for their own validation
            f.image = image
            # Pillow doesn't detect the MIME type of all formats. In those
            # cases, content_type will be None.
            f.content_type = Image.MIME.get(image.format)
        except Exception as exc:
            # Pillow doesn't recognize it as an image.
            raise ValidationError(
                self.error_messages['invalid_image'],
                code='invalid_image',
            ) from exc
        if hasattr(f, 'seek') and callable(f.seek):
            f.seek(0)
        return f


def normalize_filename(name):
    """
    Normalize filename: strip special characters that might conflict with markdown syntax
    """
    out = ''
    for c in name:
        if c in string.ascii_letters + string.digits + '-.':
            out += c
        else:
            out += '-'
    if Path(name).parent.parts:
        out = Path(name).parts[-1]
    if all(map(lambda c: c == '.', out)):
        out = 'file'
    return out


def image_contains_transparent_pixels(img):
    if 'A' not in img.getbands():
        return False

    a_band_index = img.getbands().index('A')
    return any(map(lambda d: d[a_band_index] != 255, img.getdata()))


@log_timing()
def compress_image(file, name=None):
    """
    Compress image files and convert the to JPEG.
    If the file is not an image or a SVG file, return it as-is without compressing or converting it.
    """
    if not configuration.COMPRESS_IMAGES:
        return file, name

    try:
        with Image.open(file, formats=ALLOWED_IMAGE_FORMATS) as img:
            img_format = img.format
            if img_format == 'SVG':
                raise UnidentifiedImageError('Do not compress SVG')

            # resize image to a max size
            img.thumbnail(size=(2000, 2000), resample=Image.Resampling.LANCZOS)

            # Ensure the image is correctly rotated (not rotated via EXIF info)
            img = ImageOps.exif_transpose(img)

            if img.mode not in ['RGB', 'RGBA']:
                img = img.convert('RGBA')

            # Check if image uses transparency
            out = io.BytesIO()
            if img_format in ['PNG', 'GIF'] or image_contains_transparent_pixels(img):
                # Convert to PNG and reduce quality
                img.save(out, format='PNG', optimize=True)
                file_extension = '.png'
            else:
                # Convert to JPEG and reduce quality
                img = img.convert('RGB')
                img.save(out, format='JPEG', quality=75, optimize=True)
                file_extension = '.jpg'

            # Change extension in filename
            name = name or getattr(file, 'name', None)
            if name:
                name_path = Path(name)
                if name_path.suffix:
                    name = name[:-len(name_path.suffix)] + file_extension

            if isinstance(file, File):
                return ContentFile(content=out.getvalue(), name=name or file.name), name
            else:
                out.seek(0)
                return out, name
    except UnidentifiedImageError:
        file.seek(0)
        return file, name
    except Exception:
        log.exception('Image compression error')
        raise


def get_all_file_fields():
    storage_name_map = {storages[name]: name for name in storages.backends.keys()}

    # Iterate through all models in all apps
    for model in apps.get_models():
        for field in model._meta.get_fields():
            # Check if the field is a FileField or ImageField
            if isinstance(field, models.FileField):
                yield {
                    'model': model,
                    'field': field,
                    'field_name': field.name,
                    'storage': field.storage,
                    'storage_name': storage_name_map.get(field.storage, ''),
                }

