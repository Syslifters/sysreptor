# Webhooks Plugin

This plugin adds webhooks to SysReptor. HTTP requests are sent to the configured webhooks URL when certain events occur.

## Configuration
Configure webhooks by enabling this plugin and configuring `WEBHOOKS='[...]'` in `app.env`:

```shell
ENABLED_PLUGINS="webhooks"
WEBHOOKS='[{"url": "https://example.com/webhook", "headers": [{"name": "Authorization", "value": "shared secret"}, {"name": "X-Custom-Header", "value": "other"}], "events": ["project_created", "project_finished"]}]'
```

The `events` option configures a list of events that should trigger the webhook. See [WebhookEventType in models.py](./models.py) for available events.

The `finding_updated` and `section_updated` events allow specifiying a field filter expression to only trigger the webhook if the specified field was updated. Configure the event as `<event-type>:<field-path>` e.g. `finding_updated:status`, `section_updated:data.custom_field_id`.  
Warning: Omitting the field filter, using a broad field filter (e.g. `data`) or filtering for markdown/string fields (e.g. `data.description`) is not recommended, because webhooks are triggered on every change (i.e. while typing in markdown fields).


## Requests
Webhook HTTP requests are always set as `POST` requests with a JSON body. 
HTTP headers configured in the `headers` option are added to the request (can be used authentication via a shared secret).
The body contains the event type and resource IDs, but no (potentially sensitive) data.

```json
{
    "event": "project_finished",
    "project_id": "11223344-5566-7788-9900-aabbccddeeff"
}
```

Webhook requests are retried up to 3 times in case of connection errors or on HTTP status codes 425, 429, 503.
Other HTTP status codes (e.g. 500) and timeouts (e.g. webhook took too long to process) are not retried.
