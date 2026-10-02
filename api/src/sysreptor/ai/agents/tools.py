import logging
import mimetypes
import re
import textwrap
from base64 import b64encode
from collections.abc import Callable
from functools import wraps
from typing import Annotated

from asgiref.sync import iscoroutinefunction, sync_to_async
from django.core.exceptions import ValidationError
from langchain.agents import create_agent
from langchain.messages import AIMessage, HumanMessage, ToolMessage
from langchain.tools import ToolRuntime, tool
from langgraph.errors import GraphInterrupt
from langgraph.types import Command, interrupt
from pydantic import Field

from sysreptor.ai.agents.base import (
    format_agent_error,
    get_default_model_id,
    get_model_configs,
    init_chat_model,
    to_yaml,
)
from sysreptor.ai.agents.middleware import stamp_message_timestamp
from sysreptor.ai.agents.project import ProjectContext, get_project


def agent_tool(metadata=None, **kwargs):
    def decorator(func: Callable) -> Callable:
        if not iscoroutinefunction(func):
            func = sync_to_async(func)

        @tool(**kwargs)
        @wraps(func)
        async def tool_func(*tool_args, runtime: ToolRuntime, **tool_kwargs):
            out = ToolMessage(
                content='',
                status='error',
                tool_call_id=runtime.tool_call_id,
            )
            stamp_message_timestamp(out)

            try:
                res_output = None
                res_content = await func(*tool_args, runtime=runtime, **tool_kwargs)
                if isinstance(res_content, tuple):
                    res_content, res_output = res_content
                if not isinstance(res_content, str):
                    res_content = to_yaml(res_content)
                out.content = res_content
                out.additional_kwargs['output'] = res_output or {}
                out.status = 'success'
            except GraphInterrupt:
                raise
            except Exception as ex:
                out.content = format_agent_error(ex, generic_msg=None)
                if not out.content:
                    logging.exception(ex)
                    out.content = 'Error: Unexpected error'
            return Command(update={
                'messages': [out],
            })
        tool_func.metadata = (tool_func.metadata or {}) | (metadata or {})
        return tool_func
    return decorator


@agent_tool(parse_docstring=True)
async def ask_user(
    runtime: ToolRuntime[ProjectContext],
    question: Annotated[str, Field(min_length=1)],
    options: Annotated[list[str], Field(min_length=2)],
) -> tuple[str, dict]:
    """
    Ask the user a clarifying question and wait for their answer.

    Use this when you need more information, or when there are multiple valid approaches
    and you are uncertain which to take. Prefer clear multiple-choice options. Do not use
    for routine progress updates. Ask one question at a time; call again if you need more.

    Args:
        question: The full question text shown to the user.
        options: 2 to 4 concise choice labels for the user to pick from.
    """
    answer = interrupt({
        'interrupt_type': 'ask_user',
        'question': question,
        'options': options,
    })
    if not isinstance(answer, str) or not answer.strip():
        raise ValidationError('Answer must be a non-empty string')
    content = f'User answered: {answer}'
    return content, {'answer': answer}


@agent_tool(parse_docstring=True)
async def analyze_image(
    runtime: ToolRuntime[ProjectContext],
    image: str,
    prompt: str = '',
) -> tuple[str, dict]:
    """
    Analyze a project screenshot or image with a vision model and return a text summary.

    Call this when markdown contains an image like ![](/images/name/image.png) and you
    need to read what is shown (UI text, errors, URLs, parameters, highlighted areas,
    or scene context) before writing evidence, reproduction steps, or PoC text.
    Do not guess image contents from the filename or surrounding text alone.

    Do not call again for the same image if this tool reports that image analysis is
    disabled or the model does not support image input; continue from surrounding
    text only.

    Returns a concise factual summary of visible text, highlights, and scene context.
    Use prompt when you need a specific detail answered.

    Args:
        image: Project image path from markdown, e.g. /images/name/image.png
        prompt: Optional focus question for the vision model.
            If omitted, returns a general evidence-oriented summary.
    """
    system_prompt = textwrap.dedent("""\
        You analyze pentest screenshots for report writing.
        Return a concise factual summary of visible text (errors, URLs, params, labels),
        highlighted/annotated areas, and scene context useful for evidence or reproduction.
        Quote text faithfully; do not invent unread content. Prefer short bullets. No preamble.
        If a focus question is given, answer it while still capturing important visible details.
        """)
    default_user_prompt = 'Analyze this screenshot for pentest evidence and reproduction details.'

    @sync_to_async
    def prepare():
        # Resolve vision model. Use current model if not configured.
        active_model_id = runtime.context.model or get_default_model_id()
        configs = get_model_configs()
        active_config = next((c for c in configs if c.get('id') == active_model_id), None) or {}
        vision_setting = active_config.get('vision_model')
        if vision_setting is True or 'vision_model' not in active_config:
            vision_model_id = active_model_id
        elif isinstance(vision_setting, str) and vision_setting:
            if not any(c.get('id') == vision_setting for c in configs):
                raise ValidationError(f'Image analysis failed: vision_model "{vision_setting}" is not configured.')
            vision_model_id = vision_setting
        else:
            raise ValidationError('Image analysis is disabled for the configured model.')

        # Load image
        filename = image.strip()
        if match := re.search(r'/images/name/([^)\s{]+)', filename):
            filename = match.group(1)
        if not filename or '/' in filename:
            raise ValidationError('Invalid image reference. Pass a path like /images/name/image.png')

        uploaded = get_project(runtime.context.project_id).images.filter_name(filename).get()
        with uploaded.file.open('rb') as f:
            image_bytes = f.read()

        mime_type, _ = mimetypes.guess_file_type(uploaded.name)
        if not mime_type or not mime_type.startswith('image/'):
            mime_type = 'image/png'

        prompt_text = (prompt or '').strip() or default_user_prompt
        llm = init_chat_model(vision_model_id)
        human_message = HumanMessage(content=[
            {'type': 'text', 'text': prompt_text},
            {'type': 'image', 'base64': b64encode(image_bytes).decode('ascii'), 'mime_type': mime_type},
        ])
        return llm, human_message, filename, vision_model_id

    llm, human_message, filename, vision_model_id = await prepare()
    try:
        # Nested agent so astream_events assigns a non-empty namespace (like task subagents).
        vision_agent = create_agent(
            model=llm,
            system_prompt=system_prompt,
            tools=[],
        )
        result = await vision_agent.ainvoke({'messages': [human_message]})
    except Exception as ex:
        logging.exception('analyze_image failed for %s with model %s', filename, vision_model_id)
        detail = format_agent_error(ex).removeprefix('Error: ')
        raise ValidationError(f'Image analysis failed. Maybe the model does not support images. {detail}') from ex

    ai_messages = [m for m in (result.get('messages') or []) if isinstance(m, AIMessage)]
    output = ((ai_messages[-1].text if ai_messages else '') or '').strip()
    if not output:
        raise ValidationError('Image analysis failed: empty model response.')
    return output, {'image': filename, 'model': vision_model_id}
