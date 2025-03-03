import enum


class WebhookEventType(enum.StrEnum):
    PROJECT_CREATED = 'project_created'
    PROJECT_FINISHED = 'project_finished'
    PROJECT_ARCHIVED = 'project_archived'
    PROJECT_DELETED = 'project_deleted'
    FINDING_CREATED = 'finding_created'
    FINDING_UPDATED = 'finding_updated'
    FINDING_DELETED = 'finding_deleted'
    SECTION_UPDATED = 'section_updated'

