from base64 import b64decode
import pytest
import io
import re
import pikepdf
from asgiref.sync import async_to_sync
from unittest import mock
from pytest_django.asserts import assertHTMLEqual
from django.test import override_settings

from reportcreator_api.tests.mock import create_imported_member, create_project_type, create_project, create_user, create_finding
from reportcreator_api.tasks.rendering.entry import render_pdf
from reportcreator_api.tasks.rendering.render import render_to_html
from reportcreator_api.utils.utils import merge


@pytest.mark.django_db
class TestHtmlRendering:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user()
        self.project_type = create_project_type()
        self.project = create_project(
            project_type=self.project_type, 
            members=[self.user], 
            imported_members=[create_imported_member(roles=['lead'])],
            findings_kwargs=[], 
            report_data={'field_user': str(self.user.id)})
        self.finding = create_finding(project=self.project)

        with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
            yield
    
    def render_html(self, template, additional_data={}):
        def render_only_html(data, language, **kwargs):
            html, msgs = render_to_html(template=template, styles='@import url("/assets/global/base.css");', data=merge(data, additional_data), language=language)
            return html.encode() if html else None, [m.to_dict() for m in msgs]
        
        with mock.patch('reportcreator_api.tasks.rendering.render.render_pdf', render_only_html):
            res = async_to_sync(render_pdf)(self.project)
            assert not res['messages']
            html = b64decode(res['pdf']).decode()
            return self.extract_html_part(html)

    def extract_html_part(self, html, start=None, end=None):       
        if not start and not end:
            body_start = html.index('<body')
            content_start = html.index('><div>', body_start + 1) + 6
            return html[content_start:html.index('</div></body>')]
        else:
            return html[html.index(start):html.index(end) + len(end)]

    @pytest.mark.parametrize('template,html', [
        ('{{ report.field_string }}', lambda self: self.project.data['field_string']),
        ('{{ report.field_int }}', lambda self: str(self.project.data['field_int'])),
        ('{{ report.field_enum.value }}', lambda self: self.project.data['field_enum']),
        ('{{ findings[0].cvss.vector }}', lambda self: self.finding.data['cvss']),
        ('{{ findings[0].cvss.score }}', lambda self: str(self.finding.risk_score)),
        ('{{ data.pentesters[0].name }}', lambda self: self.project.imported_members[0]['name']),
        ('<template v-for="r in data.pentesters[0].roles">{{ r }}</template>', lambda self: ''.join(self.project.imported_members[0]['roles'])),
        ('{{ data.pentesters[1].name }}', lambda self: self.user.name),
        ('<template v-for="r in data.pentesters[1].roles">{{ r }}</template>', lambda self: ''.join(self.project.members.all()[0].roles)),
        ('{{ report.field_user.id }}', lambda self: str(self.user.id)),
        ('{{ report.field_user.name }}', lambda self: self.user.name),
        ('<template v-for="f in findings">{{ f.title }}</template>', lambda self: self.finding.title),
        ('{{ capitalize("hello there") }}', "Hello there"),
        ("{{ formatDate('2022-09-21', 'iso') }}", "2022-09-21"),
        ("{{ formatDate('2022-09-21', 'short', 'de-DE') }}", "21.09.22"),
        ("{{ formatDate('2022-09-21', 'medium', 'de-DE') }}", "21.09.2022"),
        ("{{ formatDate('2022-09-21', 'long', 'de-DE') }}", "21. September 2022"),
        ("{{ formatDate('2022-09-21', 'full', 'de-DE') }}", "Mittwoch, 21. September 2022"),
        ("{{ formatDate('2022-09-21', 'short', 'en-US') }}", "9/21/22"),
        ("{{ formatDate('2022-09-21', 'medium', 'en-US') }}", "Sep 21, 2022"),
        ("{{ formatDate('2022-09-21', 'long', 'en-US') }}", "September 21, 2022"),
        ("{{ formatDate('2022-09-21', 'full', 'en-US') }}", "Wednesday, September 21, 2022"),
        ("{{ formatDate('2022-09-21', {year: '2-digit', month: 'narrow', day: '2-digit', numberingSystem: 'latn'}, 'en-US') }}", "S 21, 22"),
    ])
    def test_variables_rendering(self, template, html):
        if callable(html):
            html = html(self)
        actual_html = self.render_html(template)
        assert actual_html == html

    @pytest.mark.parametrize('template,expected', [
        ('text </p>', {'level': 'error', 'message': 'Template compilation error: Invalid end tag.'}),
        ('{{ report.nonexistent_variable.prop }}', {'level': 'error', 'message': "TypeError: Cannot read properties of undefined (reading 'prop')"}),
        ('{{ nonexistent_variable }}', {'level': 'warning', 'message': 'Property "nonexistent_variable" was accessed during render but is not defined on instance.'}),
        ('<ref to="nonexistent" />', {'level': 'warning', 'message': 'Invalid reference'}),
        ('<img src="/assets/name/nonexistent.png" />', {'level': 'warning', 'message': 'Resource not found'}),
    ])
    def test_template_error(self, template, expected):
        self.project_type.report_template = template
        res = async_to_sync(render_pdf)(project=self.project)
        assert len(res['messages']) >= 1
        msg = res['messages'][0]
        assert msg['level'] == expected['level']
        assert msg['message'] == expected['message']

    def test_markdown_rendering(self):
        assertHTMLEqual(
            self.render_html('<markdown :text="data.md" />', {'md': 'text _with_ **markdown** `code`'}), 
            '<div class="markdown"><p>text <em>with</em> <strong>markdown</strong> <code class="code-inline">code</code></p></div>'
        )
        assertHTMLEqual(
            self.render_html('<markdown>\n' + '\n'.join((' ' * 6) + l for l in [
                    '# Report title {#ref}',
                    'Paragraph _text_ with **inline** `code` and [links](https://example.com){#id .class style="color:red"}.<br>',
                    'second line [](#ref)<br>',
                    'third line',
                    '',
                    '* list item 1',
                    '* list item 2',
                    '    * list item 2.1',
                    '',
                    '> blockquote',
                    '> text',
                    '',
                    '```',
                    'code block content',
                    '    indentation preserved',
                    '<div><span>HTML</span> <strong>preserved</strong></div>',
                    '<invalid>HTML',
                    '<!-- comment preserved -->',
                    '```',
                    '',
                    '<span v-if="false">This should not be rendered</span><span v-if="report.title">Variable: {{ report.title }}</span>',
                ]) + '</markdown>'),
                '\n'.join([
                    '<div class="markdown">',
                    '<h1 id="ref">Report title</h1>',
                    '<p>Paragraph <em>text</em> with <strong>inline</strong> <code class="code-inline">code</code> and '
                        '<a href="https://example.com" id="id" class="class" style="color: red;" target="_blank" rel="nofollow noopener noreferrer">links</a>.<br>'
                        'second line <a href="#ref" class="ref ref-heading"><span class="ref-title">Report title</span></a><br>'
                        'third line</p>',
                    '<ul><li>list item 1</li><li>list item 2<ul><li>list item 2.1</li></ul></li></ul>',
                    '<blockquote><p>blockquote text</p></blockquote>'
                    '<pre class="code-block"><code class="hljs">',
                    '<span class="code-block-line" data-line-number="1">code block content</span>',
                    '<span class="code-block-line" data-line-number="2">    indentation preserved</span>',
                    '<span class="code-block-line" data-line-number="3">&lt;div&gt;&lt;span&gt;HTML&lt;/span&gt; &lt;strong&gt;preserved&lt;/strong&gt;&lt;/div&gt;</span>',
                    '<span class="code-block-line" data-line-number="4">&lt;invalid&gt;HTML</span>',
                    '<span class="code-block-line" data-line-number="5">&lt;!-- comment preserved --&gt;</span>',
                    '</code></pre>',
                    '<p><span>Variable: Report title</span></p>',
                    '</div>'
                ])
            )

    def test_toc_rendering(self):
        html = self.render_html("""
        <table-of-contents v-slot="tocItems">
            <section v-if="tocItems">
                <h1 id="toc" class="in-toc">Table of Contents</h1>
                <ul>
                    <li v-for="item in tocItems" :class="'toc-level' + item.level">
                        <ref :to="item.id" />
                    </li>
                </ul>
            </section>
        </table-of-contents>
        <h1 class="in-toc numbered" id="h1">H1</h1>
        <h2 class="in-toc numbered" id="h1.1">H1.1</h2>
        <h3 class="in-toc numbered" id="h1.1.1">H1.1.1</h3>
        <h2 class="in-toc" id="h1.2">H1.2</h2>
        <h2 class="in-toc numbered" id="h1.3">H1.3</h2>
        <h1 class="in-toc numbered" id="h2">H2</h1>
        <h2 class="in-toc numbered" id="h2.1">H2.1</h2>
        <div class="appendix">
            <h1 class="in-toc numbered" id="a">Appendix</h1>
            <h2 class="in-toc numbered" id="a.1">A.1</h2>
        </div>
        """
        )
        assertHTMLEqual(self.extract_html_part(html, '<ul>', '</ul>'), """
        <ul>
            <li class="toc-level1"><a href="#toc" class="ref ref-heading"><span class="ref-title">Table of Contents</span></a></li>
            <li class="toc-level1"><a href="#h1" class="ref ref-heading ref-heading-level1"><span class="ref-title">H1</span></a></li>
            <li class="toc-level2"><a href="#h1.1" class="ref ref-heading ref-heading-level2"><span class="ref-title">H1.1</span></a></li>
            <li class="toc-level3"><a href="#h1.1.1" class="ref ref-heading ref-heading-level3"><span class="ref-title">H1.1.1</span></a></li>
            <li class="toc-level2"><a href="#h1.2" class="ref ref-heading"><span class="ref-title">H1.2</span></a></li>
            <li class="toc-level2"><a href="#h1.3" class="ref ref-heading ref-heading-level2"><span class="ref-title">H1.3</span></a></li>
            <li class="toc-level1"><a href="#h2" class="ref ref-heading ref-heading-level1"><span class="ref-title">H2</span></a></li>
            <li class="toc-level2"><a href="#h2.1" class="ref ref-heading ref-heading-level2"><span class="ref-title">H2.1</span></a></li>
            <li class="toc-level1"><a href="#a" class="ref ref-heading ref-appendix ref-appendix-level1"><span class="ref-title">Appendix</span></a></li>
            <li class="toc-level2"><a href="#a.1" class="ref ref-heading ref-appendix ref-appendix-level2"><span class="ref-title">A.1</span></a></li>
        </ul>
        """)

    def test_chart_rendering(self):
        html = self.render_html("""
        <chart :width="15" :height="10" :config="{
            type: 'bar', 
            data: {
                labels: ['Critical', 'High', 'Medium', 'Low', 'None'],
                datasets: [{
                    data: [
                        finding_stats.count_critical,
                        finding_stats.count_high,
                        finding_stats.count_medium,
                        finding_stats.count_low,
                        finding_stats.count_info
                    ],
                    backgroundColor: ['#e21212', '#eb6020', '#cf8e2b', '#4d82a8', '#2d5f2e'],
                }]
            },
            options: {scales: {y: {beginAtZero: true, ticks: {precision: 0}}}, plugins: {legend: {display: false}}}
        }" />""")
        assert re.fullmatch(r'^\s*<img src="data:image/png;base64,[a-zA-z0-9+/=]+" alt="" style="width: 15cm; height: 10cm;">\s*$', html)

    @pytest.mark.parametrize('password,encrypted', [
        ('password', True),
        ('', False)
    ])
    def test_pdf_encryption(self, password, encrypted):
        pdf_data = b64decode(async_to_sync(render_pdf)(project=self.project, password=password)['pdf'])
        with pikepdf.Pdf.open(io.BytesIO(pdf_data), password=password) as pdf:
            assert pdf.is_encrypted == encrypted

