from django.core.exceptions import ValidationError
from django.template import Context, Engine, TemplateSyntaxError

custom_engine = Engine(
    builtins=['sysreptor_plugins.projectnumber.templatetags.random_number'],
)


def format_project_number(template: str, project_number: int) -> str:
    return custom_engine.from_string(template).render(context=Context({
        'project_number': project_number,
    }))


def validate_template(template: str):
    if not template:
        raise ValidationError('Template cannot be empty')

    try:
        format_project_number(template=template, project_number=1)
    except TemplateSyntaxError as ex:
        raise ValidationError(f'Syntax error: {ex.args}') from ex
    except Exception as ex:
        raise ValidationError(f'Error in template: {ex}') from ex

