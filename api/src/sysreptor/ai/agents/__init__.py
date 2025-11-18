import functools

from sysreptor.ai.agents.base import agent_stream, get_chat_history
from sysreptor.ai.agents.project import init_agent_project_agent, init_agent_project_ask
from sysreptor.utils import license


@functools.cache
def get_agent(agent: str):
    community_agents = {
        'project_ask': init_agent_project_ask,
    }
    pro_agents = {
        'project_agent': init_agent_project_agent,
    }

    init_agent = (community_agents | pro_agents).get(agent)
    if not init_agent:
        raise ValueError(f'Unknown agent "{agent}"')

    if agent in pro_agents and not license.is_professional():
        raise license.LicenseError(f'Professional license required for agent "{agent}"')

    return init_agent()


__all__ = [
    'get_agent',
    'agent_stream',
    'get_chat_history',
]
