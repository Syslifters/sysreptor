import enum


class WebhookEventType(enum.StrEnum):
    PROJECT_CREATED = 'project_created'
    PROJECT_FINISHED = 'project_finished'
    PROJECT_ARCHIVED = 'project_archived'
    PROJECT_DELETED = 'project_deleted'
    FINDING_CREATED = 'finding_created'
    FINDING_DELETED = 'finding_deleted'

    # Following events allow specifying field filters via "<event-type>:<field-path>"
    # e.g. "finding_updated:status", "section_updated:data.custom_field_id"
    # Warning: 
    # * do not omit field filters
    # * do not use broad field filters (e.g. "data")
    # * do not target markdown/string fields (e.g. "data.description")
    # because webhooks are triggered on every change (i.e. while typing in markdown fields).
    FINDING_UPDATED = 'finding_updated'
    SECTION_UPDATED = 'section_updated'

