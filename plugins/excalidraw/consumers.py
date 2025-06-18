
import logging

from channels.db import database_sync_to_async
from django.utils import timezone
from sysreptor.pentests.consumers import CollabConsumerBase
from sysreptor.pentests.models import CollabEvent, PentestProject
from sysreptor.plugins import configuration

from .models import ProjectExcalidrawData


class ExcalidrawConsumer(CollabConsumerBase):
    initial_path = 'excalidraw'

    async def get_related_id(self):
        return self.scope['url_route']['kwargs']['project_pk']

    @property
    def group_name(self) -> str:
        return f'excalidraw_{self.related_id}'
    
    def has_permission(self, action=None, **kwargs):
        project = self.get_project()
        if not self.user or not project:
            return False
        if action in ['connect', 'read']:
            return True
        elif action in ['write']:
            if project.readonly:
                return False
            elif self.user.is_guest and not configuration.GUEST_USERS_CAN_EDIT_PROJECTS and not self.user.is_admin and not self.user.is_project_admin:
                return False
            return True
    
    def get_project(self):
        return PentestProject.objects \
            .only_permitted(self.user) \
            .filter(id=self.related_id) \
            .first()
    
    @database_sync_to_async
    def get_initial_message(self):
        db_data = ProjectExcalidrawData.objects \
            .filter(project_id=self.related_id) \
            .first()
        return {
            'type': 'collab.init',
            'client_id': self.client_id,
            'elements': db_data.elements if db_data else [],
            'clients': self.get_client_infos(),
            'permissions': {
                'read': True,
                'write': self.has_permission(action='write'),
            },
        }

    async def receive_json(self, content, **kwargs):
        event = None
        match content.get('type'):
            case 'collab.update_excalidraw':
                event = await self.collab_update_excalidraw(content)
            case _:
                raise ValueError(f'Invalid message type: {content.get("type")}')
        await self.send_colllab_event(event)

    async def collab_update_excalidraw(self, content):
        elements = content.get('elements', [])
        syncall = content.get('syncall', False)

        timestamp = timezone.now()
        event = CollabEvent(
            related_id=self.related_id,
            path=self.initial_path,
            type='collab.update_excalidraw',
            created=timestamp,
            version=timestamp.timestamp(),
            client_id=self.client_id,
            data={
                'elements': elements,
                'syncall': syncall,
            },
        )

        @database_sync_to_async
        def db_handler():
            if syncall:
                # Update DB entries
                logging.info(f'collab_update_excalidraw syncall: {content}')
                ProjectExcalidrawData.objects.update_or_create(
                    project_id=self.related_id,
                    defaults={'elements': elements},
                    create_defaults={'elements': elements},
                )

            event.save()
            return event

        max_message_size =  1024 * 1024 - 100  # 1MB without wrapper size
        if syncall or len(await self.encode_json(event.to_dict())) > max_message_size:
            # Save to DB when the message is too large
            return await db_handler()
        else:
            # Skip initializing a DB connection if not needed to improve performance
            return event.to_dict()
