import asyncio
import logging

import httpx
import tenacity
from sysreptor.plugins import configuration
from sysreptor.utils.utils import run_in_background

from .models import WebhookEventType


@tenacity.retry(
    retry=tenacity.retry_if_exception_type((httpx.ConnectError, httpx.ConnectTimeout)),
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_fixed(1),
)
async def send_webhook_request(client: httpx.AsyncClient, webhook, data):
    logging.info(f'Sending webhook url={webhook["url"]} {data=}')
    response = await client.post(url=webhook['url'], json=data, headers=[(h.get('name'), h.get('value')) for h in (webhook.get('headers') or [])])
    if response.status_code in [425, 429, 503]:
        raise tenacity.TryAgain()
    response.raise_for_status()
    return response


async def send_webhook_requests(data, webhooks_to_send):
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=False) as client:
            request_tasks = []
            for webhook in webhooks_to_send:
                request_tasks.append(send_webhook_request(client=client, webhook=webhook, data=data))
            res = await asyncio.gather(*request_tasks, return_exceptions=True)
            exceptions = [r for r in res if isinstance(r, Exception)]
            if exceptions:
                raise ExceptionGroup('Webhook errors', exceptions)  # noqa: F821
    except Exception as ex:
        logging.exception(ex)


async def send_webhooks(event_type: WebhookEventType, data):
    webhook_settings = await configuration.aget('WEBHOOKS') or []
    webhooks_to_send = []
    for webhook in webhook_settings:
        for e in webhook.get('events', []):
            s = e.split(':', 1)
            e_type = s[0]
            e_field = s[1] if len(s) > 1 else None
            fields = data.get('fields', [])
            if e_type == event_type and (
                not e_field or 
                any(f == e_field or f.startswith(e_field + '.') for f in fields)
            ):
                webhooks_to_send.append(webhook)
                break

    if webhooks_to_send:
        run_in_background(send_webhook_requests)(data | {'event': event_type.value}, webhooks_to_send)

