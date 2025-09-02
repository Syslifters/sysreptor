from django import template

register = template.Library()

@register.tag
def noemptylines(parser, token):
    nodelist = parser.parse(("endnoemptylines",))
    parser.delete_first_token()
    return NoEmptyLinesNode(nodelist)


class NoEmptyLinesNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        output = self.nodelist.render(context)
        rendered = []
        for line in output.splitlines():
            if line.strip():
                rendered.append(line)
        return "\n".join(rendered)
    
@register.tag
def oneliner(parser, token):
    nodelist = parser.parse(("endoneliner",))
    parser.delete_first_token()
    return OnelinerNode(nodelist)


class OnelinerNode(NoEmptyLinesNode):
    def render(self, context):
        rendered = super().render(context)
        return rendered.replace('\n', ' ')