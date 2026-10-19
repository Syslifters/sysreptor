from uuid import uuid4

from asgiref.sync import async_to_sync
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.utils import termcolors
from langchain.messages import HumanMessage
from langgraph.types import Command as ResumeCommand

from sysreptor.ai.agents import agent_stream, get_agent
from sysreptor.ai.agents.project import get_project
from sysreptor.ai.models import ChatThread
from sysreptor.users.models import PentestUser
from sysreptor.utils import license


def get_prompts(stdout):
    while True:
        try:
            prompt = input('> ')
        except (EOFError, KeyboardInterrupt):
            break
        if prompt:
            yield prompt


class Command(BaseCommand):
    help = 'Test the SysReptor AI chat'

    def add_arguments(self, parser):
        parser.add_argument('--user', type=str, required=True, help='Username to run the agent as')
        parser.add_argument('--project', type=str, required=True, help='Project ID to run the agent in')
        parser.add_argument('--agent', type=str, default='project_ask', help='Agent to use')
        parser.add_argument('--model', type=str, default=None, help='Model ID to use')
        return super().add_arguments(parser)

    def handle(self, user, project, agent, model, *args, **options):
        try:
            agent = get_agent(agent)
            user = PentestUser.objects.get(username=user)
            project = get_project(project, prefetch=True)
            thread = ChatThread.objects.create(user=user, project=project)
        except (ObjectDoesNotExist, license.LicenseError) as ex:
            raise CommandError(str(ex)) from ex

        self.stdout.write(self.style.SUCCESS(f'=== SysReptor AI Chat (Thread: {thread.id}) ==='))
        for prompt in get_prompts(stdout=self.stdout):
            async_to_sync(self.run_agent)(
                agent=agent,
                thread=thread,
                prompt=prompt,
                model=model,
            )

    async def run_agent(self, agent, thread, prompt, model=None):
        input_data = {
            'messages': [HumanMessage(id=str(uuid4()), content=prompt)],
        }
        while True:
            resume = await self.stream_events(agent=agent, thread=thread, input_data=input_data, model=model)
            if not resume:
                break
            input_data = ResumeCommand(resume=resume)

    async def stream_events(self, agent, thread, input_data, model=None) -> dict | None:
        prev_token = None
        tool_calls = {}
        streamed_ids = set()
        resume = None

        async for token in agent_stream(
            agent=agent,
            thread=thread,
            input=input_data,
            model=model,
        ):
            if token.get('subagent'):
                continue

            match token['type']:
                case 'text':
                    content = token['content']
                    if content.get('role') == 'user':
                        continue
                    msg_id = content.get('id')
                    if content.get('replace') and msg_id in streamed_ids:
                        # Message already printed while streaming
                        continue
                    if content.get('reasoning'):
                        if not prev_token or prev_token['type'] != 'text' or prev_token['content'].get('id') != msg_id:
                            self.newline_if_needed(prev_token)
                            self.stdout.write(self.style_reasoning('Reasoning: '), ending='')
                        self.stdout.write(self.style_reasoning(str(content['reasoning'])), ending='')
                    if content.get('text'):
                        if prev_token and prev_token['type'] == 'text' and prev_token['content'].get('reasoning'):
                            self.newline_if_needed(prev_token)
                        self.stdout.write(str(content['text']), ending='')
                    if msg_id and (content.get('text') or content.get('reasoning')):
                        streamed_ids.add(msg_id)
                    prev_token = token
                case 'tool_call':
                    tool_calls[token['content']['id']] = token
                case 'tool_call_status':
                    prev = tool_calls.pop(token['content']['id'], {}).get('content', {})
                    tc = prev | token['content']
                    self.newline_if_needed(prev_token)
                    color = self.style.ERROR if tc.get('status') == 'error' else self.style.SUCCESS
                    name = tc.get('name', '?')
                    args = tc.get('args', {})
                    status = token['content'].get('status')
                    self.stdout.write(color(f'[Tool Call: {name}({args}) - {status}]'))
                    prev_token = token
                case 'interrupt':
                    self.newline_if_needed(prev_token)
                    resume = {}
                    for item in token['content']:
                        interrupt_id = item['id']
                        value = item.get('value') or {}
                        question = value.get('question') or str(value)
                        options = value.get('options') or []
                        self.stdout.write(self.style.WARNING(f'[Interrupt] {question}'))
                        if options:
                            self.stdout.write(self.style.WARNING(f'  Options: {", ".join(str(o) for o in options)}'))
                        try:
                            answer = input('Answer> ')
                        except (EOFError, KeyboardInterrupt):
                            answer = ''
                        resume[interrupt_id] = answer
                    prev_token = token
                case 'error':
                    self.newline_if_needed(prev_token)
                    self.stdout.write(self.style.ERROR(f'[Error: {token["content"]}]'))
                    prev_token = token
                case 'metadata' | 'snapshot' | 'run_status':
                    pass
                case _:
                    self.stdout.write(self.style.WARNING(f'[Unknown Token: {token}]'))

        self.newline_if_needed(prev_token)
        self.stdout.write('')
        return resume

    def newline_if_needed(self, prev_token=None):
        if prev_token and prev_token['type'] == 'text' and \
           not (prev_token['content'].get('reasoning', '') or prev_token['content'].get('text', '')).endswith('\n'):
            self.stdout.write('')

    def style_reasoning(self, text: str) -> str:
        return termcolors.colorize(text, fg='cyan')
