import asyncio

import httpx
import tenacity
from django.apps import apps
from reportcreator_api.utils.utils import run_in_background

from .app import WebhooksPluginConfig


@tenacity.retry(
    retry=tenacity.retry_if_exception_type((httpx.ConnectError, httpx.ConnectTimeout)), 
    stop=tenacity.stop_after_attempt(3), 
    wait=tenacity.wait_fixed(1)
)
async def send_webhook_request(client: httpx.AsyncClient, webhook_config, data):
    # TODO: security considerations: are custom headers dangerous?
    response = await client.post(url=webhook_config['url'], json=data, headers=webhook_config.get('headers', {}))
    if response.status_code in [425, 429, 503]:
        raise tenacity.TryAgain()
    return response


async def send_webhook_requests(data, webhooks_to_send):
    # print('send_webhook_requests before')
    # try:
    #     await asyncio.sleep(0.1)
    # except asyncio.CancelledError:
    #     print('send_webhook_requests cancel')
    #     logging.exception('send_webhook_requests cancelled')
    #     raise
    # print('send_webhook_requests after')

    async with httpx.AsyncClient(timeout=10) as client:
        request_tasks = []
        for webhook in webhooks_to_send:
            request_tasks.append(send_webhook_request(client=client, webhook=webhook, data=data))
        await asyncio.gather(*request_tasks, return_exceptions=True)


async def send_webhooks(event_name, data):
    webhook_settings = apps.get_app_config(WebhooksPluginConfig.label).settings.get('WEBHOOKS', [])

    webhooks_to_send = list(filter(lambda w: event_name in w.get('events', []), webhook_settings))
    if webhooks_to_send:
        run_in_background(send_webhook_requests(data | {'event': event_name}, webhooks_to_send))

