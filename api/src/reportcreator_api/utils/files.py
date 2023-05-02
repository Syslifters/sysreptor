import string
import io
import logging
from django.conf import settings
from pathlib import Path
from PIL import Image, ImageOps, UnidentifiedImageError
from django.core.files.base import ContentFile, File
from reportcreator_api.utils.logging import log_timing


log = logging.getLogger(__name__)


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


@log_timing
def compress_image(file, name=None):
    """
    Compress image files and convert the to JPEG.
    If the file is not an image or a SVG file, return it as-is without compressing or converting it.
    """
    if not settings.COMPRESS_IMAGES:
        return file, name

    try:
        with Image.open(file) as img:
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
    except Exception as ex:
        if not isinstance(ex, UnidentifiedImageError):
            log.exception('Image compression error')
        file.seek(0)
        return file, name

