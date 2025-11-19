
from asgiref.sync import async_to_sync
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.utils import termcolors

from sysreptor.ai.agents import agent_stream, get_agent
from sysreptor.ai.agents.project import get_project
from sysreptor.ai.models import ChatThread
from sysreptor.users.models import PentestUser
from sysreptor.utils import license


def get_prompts(stdout):
    while True:
        try:
            prompt = input('> ')
        except EOFError:
            break
        if prompt:
            yield prompt


class Command(BaseCommand):
    help = 'Test the SysReptor AI chat'

    def add_arguments(self, parser):
        parser.add_argument('--user', type=str, required=True, help='Username to run the agent as')
        parser.add_argument('--project', type=str, required=True, help='Project ID to run the agent in')
        parser.add_argument('--agent', type=str, default='project_ask', help='Agent to use')
        return super().add_arguments(parser)

    def handle(self, user, project, agent, *args, **options):
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
            )

    async def run_agent(self, agent, thread, prompt):
        prev_token = None
        tool_calls = {}
        async for token in agent_stream(
            agent=agent,
            thread=thread,
            input={'messages': [prompt]},
        ):
            # print('\nToken', token)

            match token['type']:
                case 'text':
                    if token['content'].get('reasoning'):
                        if not prev_token or prev_token['type'] != 'text' or prev_token['content']['id'] != token['content']['id']:
                            self.newline_if_needed(prev_token)
                            self.stdout.write(self.style_reasoning('Reasoning: '), ending='')
                        self.stdout.write(self.style_reasoning(str(token['content']['reasoning'])), ending='')
                    if token['content'].get('text'):
                        if prev_token and prev_token['type'] == 'text' and prev_token['content'].get('reasoning'):
                            self.newline_if_needed(prev_token)
                        self.stdout.write(str(token['content']['text']), ending='')
                    prev_token = token
                case 'tool_call':
                    tool_calls[token['content']['id']] = token
                case 'tool_call_status':
                    tc = tool_calls.pop(token['content']['id'], {})['content'] | token['content']

                    self.newline_if_needed(prev_token)
                    color = self.style.ERROR if tc['status'] == 'error' else self.style.SUCCESS
                    self.stdout.write(color(f'[Tool Call: {tc["name"]}({tc["args"]}) - {token["content"]["status"]}]'))
                    prev_token = token
                case 'metadata':
                    pass
                case _:
                    self.stdout.write(self.style.WARNING(f'[Unknown Token: {token}]'))
        self.newline_if_needed(prev_token)
        self.stdout.write('')

    def newline_if_needed(self, prev_token=None):
        if prev_token and prev_token['type'] == 'text' and \
           not (prev_token['content'].get('reasoning', '') or prev_token['content'].get('text', '')).endswith('\n'):
            self.stdout.write('')

    def style_reasoning(self, text: str) -> str:
        return termcolors.colorize(text, fg='cyan')
