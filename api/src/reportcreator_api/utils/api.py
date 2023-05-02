from asgiref.sync import sync_to_async
from django.http import FileResponse, Http404
from django.core.exceptions import PermissionDenied
from adrf.views import APIView as AsyncAPIView
from rest_framework import exceptions, status, views, generics, viewsets
from rest_framework.response import Response

from reportcreator_api.utils import license


class GenericAPIViewAsync(generics.GenericAPIView, AsyncAPIView):
    _action = None

    @property
    def action(self):
        return self._action
    
    @action.setter
    def action(self, value):
        self._action = value

    async def aget_valid_serializer(self, *args, **kwargs):
        serializer = self.get_serializer(*args, **kwargs)
        await sync_to_async(serializer.is_valid)(raise_exception=True)
        return serializer

    async def aget_object(self):
        return await sync_to_async(super().get_object)()


class FileResponseAsync(FileResponse):
    async def to_async_iterator(self, sync_iter):
        for chunk in await sync_to_async(list)(sync_iter):
            yield chunk

    def _set_streaming_content(self, value):
        if not hasattr(value, "read"):
            self.file_to_stream = None
            return super()._set_streaming_content(self.to_async_iterator(value))
        
        self.file_to_stream = filelike = value
        if hasattr(filelike, "close"):
            self._resource_closers.append(filelike.close)
        value = iter(lambda: filelike.read(self.block_size), b"")
        self.set_headers(filelike)
        super()._set_streaming_content(self.to_async_iterator((value)))


def exception_handler(exc, context):
    """
    Returns the response that should be used for any given exception.
    By default we handle the REST framework `APIException`, and also
    Django's built-in `Http404` and `PermissionDenied` exceptions.
    Any unhandled exceptions may return `None`, which will cause a 500 error
    to be raised.
    """
    if isinstance(exc, Http404):
        exc = exceptions.NotFound(*(exc.args))
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied(*(exc.args))
    elif isinstance(exc, license.LicenseError):
        exc = exceptions.PermissionDenied(detail=exc.detail, code='license')

    if isinstance(exc, exceptions.APIException):
        headers = {}
        if getattr(exc, 'auth_header', None):
            headers['WWW-Authenticate'] = exc.auth_header
        if getattr(exc, 'wait', None):
            headers['Retry-After'] = '%d' % exc.wait

        if isinstance(exc.detail, (list, dict)):
            data = exc.detail
        else:
            data = {'detail': exc.detail, 'code': exc.detail.code}

        views.set_rollback()
        return Response(data, status=exc.status_code, headers=headers)

    return None