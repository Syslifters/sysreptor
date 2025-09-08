import contextlib
import re
from unittest import mock

from django.template import Context, Engine
from django.template.base import Token, TokenType
from html_to_markdown import convert_to_markdown
from lxml import etree
from sysreptor.pentests.cvss.cvss2 import is_cvss2, parse_cvss2


def parse_xml(file):
    file.seek(0)
    data = file.read().lstrip()
    tree = etree.fromstring(data, etree.XMLParser(
        resolve_entities=False,
        recover=True,
    ))

    if tree is None:
        raise etree.XMLSyntaxError("Could not parse XML", 0, 0, 0)

    return tree


def xml_to_dict(node):
    """
    Convert an lxml.etree node tree into a dict.
    """
    result = {}

    for key, value in node.attrib.items():
        result['@' + key] = value

    for element in node.iterchildren():
        # Remove namespace prefix
        key = etree.QName(element).localname

        # Process element as tree element if the inner XML contains non-whitespace content
        if element.text and element.text.strip():
            value = element.text
        else:
            value = xml_to_dict(element)
        if key in result:
            if type(result[key]) is list:
                result[key].append(value)
            else:
                result[key] = [result[key], value]
        else:
            result[key] = value
    return result


def html_to_markdown(html: str, **kwargs) -> str:
    return convert_to_markdown(
        source=html, 
        extract_metadata=False,
        heading_style="atx",
        bullets="*",
        escape_misc=False,
        preprocess_html=True,
        **kwargs
    )


@contextlib.contextmanager
def custom_django_tags():
    """
    Monkey-patch django template engine to use different delimiters.
    """

    # Modified django template language tags
    HTML_REGEX = re.compile(r"(<!--{%.*?%}-->|<!--{{.*?}}-->|<!--{#.*?#}-->)")
    BLOCK_TAG_START = "<!--{%"
    BLOCK_TAG_END = "%}-->"
    VARIABLE_TAG_START = "<!--{{"
    VARIABLE_TAG_END = "}}-->"
    COMMENT_TAG_START = "<!--{#"
    COMMENT_TAG_END = "#}-->"

    def create_token(self, token_string, position, lineno, in_tag):
        """
        Convert the given token string into a new Token object and return it.
        If in_tag is True, we are processing something that matched a tag,
        otherwise it should be treated as a literal string.
        """
        if in_tag:
            # The [0:2] and [2:-2] ranges below strip off *_TAG_START and
            # *_TAG_END. The 2's are hard-coded for performance. Using
            # len(BLOCK_TAG_START) would permit BLOCK_TAG_START to be
            # different, but it's not likely that the TAG_START values will
            # change anytime soon.
            token_start = token_string[0:len(BLOCK_TAG_START)]
            if token_start == BLOCK_TAG_START:
                content = token_string[len(BLOCK_TAG_START):-len(BLOCK_TAG_END)].strip()
                if self.verbatim:
                    # Then a verbatim block is being processed.
                    if content != self.verbatim:
                        return Token(TokenType.TEXT, token_string, position, lineno)
                    # Otherwise, the current verbatim block is ending.
                    self.verbatim = False
                elif content[:9] in ("verbatim", "verbatim "):
                    # Then a verbatim block is starting.
                    self.verbatim = "end%s" % content
                return Token(TokenType.BLOCK, content, position, lineno)
            if not self.verbatim:
                content = token_string[len(BLOCK_TAG_START):-len(BLOCK_TAG_END)].strip()
                if token_start == VARIABLE_TAG_START:
                    return Token(TokenType.VAR, content, position, lineno)
                # BLOCK_TAG_START was handled above.
                assert token_start == COMMENT_TAG_START
                return Token(TokenType.COMMENT, content, position, lineno)
        return Token(TokenType.TEXT, token_string, position, lineno)

    with mock.patch('django.template.base.Lexer.create_token', create_token), \
        mock.patch('django.template.base.tag_re', HTML_REGEX), \
        mock.patch('django.template.base.BLOCK_TAG_START', BLOCK_TAG_START), \
        mock.patch('django.template.base.BLOCK_TAG_END', BLOCK_TAG_END), \
        mock.patch('django.template.base.VARIABLE_TAG_START', VARIABLE_TAG_START), \
        mock.patch('django.template.base.VARIABLE_TAG_END', VARIABLE_TAG_END), \
        mock.patch('django.template.base.COMMENT_TAG_START', COMMENT_TAG_START), \
        mock.patch('django.template.base.COMMENT_TAG_END', COMMENT_TAG_END):
        yield


@custom_django_tags()
def load_template_string(template_string: str):
    return Engine(
        builtins=Engine.default_builtins + ['sysreptor_plugins.scanimport.templatetags'],
        autoescape=False
    ).from_string(template_string)


@custom_django_tags()
def render_template_string(template_string: str, context: dict) -> str:
    return load_template_string(template_string) \
        .render(context=Context(context, autoescape=False))


def cvss2_to_cvss31(cvss2_vector):
    if not is_cvss2(cvss2_vector):
        return cvss2_vector
    
    metrics2 = parse_cvss2(cvss2_vector)
    impact_mapping = {'C': 'H', 'P': 'L', 'N': 'N'}
    metrics3 = {
        'AV': metrics2['AV'],
        'AC': {'M': 'L'}.get(metrics2['AC'], metrics2['AC']),
        'PR': {"M": "H", "S": "L", "N": "N"}[metrics2.get('Au', 'N')],
        'UI': 'N',
        'S': 'U',
        'C': impact_mapping.get(metrics2['C'], 'N'),
        'I': impact_mapping.get(metrics2['I'], 'N'),
        'A': impact_mapping.get(metrics2['A'], 'N')
    }
    return 'CVSS:3.1' + ''.join([f"/{k}:{v}" for k, v in metrics3.items()])
