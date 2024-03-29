from functools import reduce
import json
import operator
from types import NoneType
from asgiref.sync import sync_to_async
from django.conf import settings
from django.db.models import Q, OrderBy
from django.http import StreamingHttpResponse, FileResponse, Http404
from django.core.exceptions import PermissionDenied
from django.utils.functional import classproperty
from adrf.views import APIView as AsyncAPIView
from adrf.viewsets import ViewSet as AdrfAsyncViewSet
from rest_framework import exceptions, views, generics, pagination
from rest_framework.response import Response

from reportcreator_api.archive.crypto import CryptoError
from reportcreator_api.utils import license


class GenericAPIViewAsyncMixin:
    throttle_scope = None

    async def aget_valid_serializer(self, *args, **kwargs):
        serializer = self.get_serializer(*args, **kwargs)
        await sync_to_async(serializer.is_valid)(raise_exception=True)
        return serializer

    async def aget_object(self):
        return await sync_to_async(super().get_object)()


class GenericAPIViewAsync(GenericAPIViewAsyncMixin, generics.GenericAPIView, AsyncAPIView):
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


class ViewSetAsync(GenericAPIViewAsyncMixin, AdrfAsyncViewSet):
    @classproperty
    def view_is_async(cls):
        return True


class _SyncIterableToAsync:
    def __init__(self, get_sync_iterable):
        """
        Functions as an async version of the iterable returned by ``get_sync_iterable``.
        """

        self.get_sync_iterable = get_sync_iterable

        # async versions of the `next` and `iter` functions
        self.next_async = sync_to_async(self.next)
        self.iter_async = sync_to_async(iter)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not hasattr(self, "sync_iterator"):
            # one-time setup of the internal iterator
            sync_iterable = await self.get_sync_iterable()
            self.sync_iterator = await self.iter_async(sync_iterable)

        return await self.next_async(self.sync_iterator)

    @staticmethod
    def next(it):
        """
        asyncio expects `StopAsyncIteration` in place of `StopIteration`,
        so here's a modified in-built `next` function that can handle this.
        """
        try:
            return next(it)
        except StopIteration:
            raise StopAsyncIteration


def sync_iterable_to_async(sync_iterable):
    async def get_sync_iterable():
        return sync_iterable
    return _SyncIterableToAsync(get_sync_iterable)


class StreamingHttpResponseAsync(StreamingHttpResponse):
    async def __aiter__(self):
        try:
            async for part in self.streaming_content:
                yield part
        except TypeError:
            async for part in sync_iterable_to_async(self.streaming_content):
                yield part


class FileResponseAsync(FileResponse):
    block_size = settings.FILE_UPLOAD_MAX_MEMORY_SIZE

    async def __aiter__(self):
        try:
            async for part in self.streaming_content:
                yield part
        except TypeError:
            async for part in sync_iterable_to_async(self.streaming_content):
                yield part


class CursorMultiPagination(pagination.CursorPagination):
    """
    Cursor pagination that supports ordering by multiple fields.
    Uses all order_by fields in the cursor, not just the first one.
    """

    def get_ordering(self, request, queryset, view):
        return queryset.query.order_by if queryset.ordered else self.ordering

    def _get_position_from_instance(self, instance, ordering):
        out = []
        for field_name in ordering:
            if isinstance(field_name, OrderBy):
                field_name = field_name.expression.name

            field_value = instance
            for k in field_name.lstrip('-').split('__'):
                if isinstance(instance, dict):
                    field_value = field_value[k]
                else:
                    field_value = getattr(field_value, k)
            out.append(field_value if isinstance(field_value, (str, bool, int, float, NoneType)) else str(field_value))
        return json.dumps(out)

    def paginate_queryset(self, queryset, request, view=None):
        self.page_size = self.get_page_size(request)
        if not self.page_size:
            return None

        self.base_url = request.build_absolute_uri()
        self.ordering = self.get_ordering(request, queryset, view)

        self.cursor = self.decode_cursor(request)
        if self.cursor is None:
            (offset, reverse, current_position) = (0, False, None)
        else:
            (offset, reverse, current_position) = self.cursor

        # Cursor pagination always enforces an ordering.
        if reverse:
            queryset = queryset.order_by(*pagination._reverse_ordering(self.ordering))
        else:
            queryset = queryset.order_by(*self.ordering)

        # If we have a cursor with a fixed position then filter by that.
        if current_position is not None:
            current_position_list = json.loads(current_position)

            q_objects_equals = {}
            q_objects_compare = {}

            for order, position in zip(self.ordering, current_position_list):
                if isinstance(order, OrderBy):
                    is_reversed = order.descending
                    order_attr = order.expression.name
                else:
                    is_reversed = order.startswith("-")
                    order_attr = order.lstrip("-")

                q_objects_equals[order] = Q(**{order_attr: position})

                # Test for: (cursor reversed) XOR (queryset reversed)
                if self.cursor.reverse != is_reversed:
                    q_objects_compare[order] = Q(
                        **{(order_attr + "__lt"): position}
                    )
                else:
                    q_objects_compare[order] = Q(
                        **{(order_attr + "__gt"): position}
                    )

            filter_list = []
            # starting with the second field
            for i in range(len(self.ordering)):
                # The first operands need to be equals
                # the last operands need to be gt
                equals = list(self.ordering[:i+1])
                greater_than_q = q_objects_compare[equals.pop()]
                sub_filters = [q_objects_equals[e] for e in equals]
                sub_filters.append(greater_than_q)
                filter_list.append(reduce(operator.and_, sub_filters))

            queryset = queryset.filter(reduce(operator.or_, filter_list))

        # If we have an offset cursor then offset the entire page by that amount.
        # We also always fetch an extra item in order to determine if there is a
        # page following on from this one.
        results = list(queryset[offset:offset + self.page_size + 1])
        self.page = list(results[:self.page_size])

        # Determine the position of the final item following the page.
        if len(results) > len(self.page):
            has_following_position = True
            following_position = self._get_position_from_instance(results[-1], self.ordering)
        else:
            has_following_position = False
            following_position = None

        if reverse:
            # If we have a reverse queryset, then the query ordering was in reverse
            # so we need to reverse the items again before returning them to the user.
            self.page = list(reversed(self.page))

            # Determine next and previous positions for reverse cursors.
            self.has_next = (current_position is not None) or (offset > 0)
            self.has_previous = has_following_position
            if self.has_next:
                self.next_position = current_position
            if self.has_previous:
                self.previous_position = following_position
        else:
            # Determine next and previous positions for forward cursors.
            self.has_next = has_following_position
            self.has_previous = (current_position is not None) or (offset > 0)
            if self.has_next:
                self.next_position = following_position
            if self.has_previous:
                self.previous_position = current_position

        # Display page controls in the browsable API if there is more
        # than one page.
        if (self.has_previous or self.has_next) and self.template is not None:
            self.display_page_controls = True

        return self.page


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
    elif isinstance(exc, CryptoError):
        exc = exceptions.APIException(detail=exc.args, code='crypto')
    elif isinstance(exc, TimeoutError):
        exc = exceptions.APIException(detail=exc.args, code='timeout')

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
