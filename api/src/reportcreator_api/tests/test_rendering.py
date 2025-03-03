import io
import re
from unittest import mock

import pikepdf
import pytest
from asgiref.sync import async_to_sync
from django.test import override_settings
from pytest_django.asserts import assertHTMLEqual

from reportcreator_api.pentests import cvss
from reportcreator_api.tasks.rendering.entry import render_pdf, render_project_markdown_fields_to_html
from reportcreator_api.tasks.rendering.render import render_pdf_impl
from reportcreator_api.tests.mock import (
    create_finding,
    create_imported_member,
    create_png_file,
    create_project,
    create_project_type,
    create_user,
    update,
)
from reportcreator_api.utils.utils import copy_keys, merge


def html_load_script(src):
    return f"""<teleport to="head"><component is="script" src="{src}" type="text/javascript" /></teleport>"""


@pytest.mark.xdist_group('rendering')
@pytest.mark.django_db()
class TestHtmlRendering:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user()
        self.project_type = create_project_type(assets_kwargs=[
            {'name': 'image.png', 'content': create_png_file()},
            {'name': 'test.js', 'content': b'console.log("Script loaded");'},
        ])
        self.project = create_project(
            project_type=self.project_type,
            members=[self.user],
            imported_members=[create_imported_member(roles=['lead'])],
            findings_kwargs=[],
            images_kwargs=[{'name': 'image.png'}],
            files_kwargs=[{'name': 'file.pdf'}],
            report_data={'field_user': str(self.user.id)})
        self.finding = create_finding(project=self.project)

        with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
            yield

    def render_html(self, template, additional_data=None):
        async def render_only_html(data, language, **kwargs):
            return await render_pdf_impl(
                template=template,
                styles='@import url("/assets/global/base.css");',
                data=merge(data, additional_data or {}),
                resources={},
                language=language,
                output='html',
            )

        with mock.patch('reportcreator_api.tasks.rendering.render.render_pdf_impl', render_only_html):
            res = async_to_sync(render_pdf)(self.project)
            assert not res.messages
            html = res.pdf.decode()
            return self.extract_html_part(html)

    def extract_html_part(self, html, start=None, end=None):
        if not start and not end:
            body_start = html.index('<body')
            content_start = html.index('><div>', body_start + 1) + 6
            return html[content_start:html.index('</div></body>')]
        else:
            return html[html.index(start):html.index(end) + len(end)]

    @pytest.mark.parametrize(("template", "html"), [
        ('{{ report.field_string }}', lambda self: self.project.data['field_string']),
        ('{{ report.field_int }}', lambda self: str(self.project.data['field_int'])),
        ('{{ report.field_enum.value }}', lambda self: self.project.data['field_enum']),
        ('{{ findings[0].cvss.vector }}', lambda self: self.finding.data['cvss']),
        ('{{ findings[0].cvss.score }}', lambda self: str(cvss.calculate_score(self.finding.data['cvss']))),
        ('{{ findings[0].created }}', lambda self: self.finding.created.isoformat()),
        ('{{ report.field_cwe.value }} {{ report.field_cwe.id }} {{ report.field_cwe.name }}', "CWE-89 89 Improper Neutralization of Special Elements used in an SQL Command ('SQL Injection')"),
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
        ("""{{ (helperFunction = function () { return report.title + ' function'; }, null) }}{{ helperFunction() }}""", lambda self: f"{self.project.data['title']} function"),
        ("""{{ (computedVar = computed(() => report.title + ' computed'), null) }}{{ computedVar.value }}""", lambda self: f"{self.project.data['title']} computed"),
    ])
    def test_variables_rendering(self, template, html):
        if callable(html):
            html = html(self)
        actual_html = self.render_html(template)
        assert actual_html == html

    @pytest.mark.parametrize(("template", "expected"), [
        ('text </p>', {'level': 'error', 'message': 'Template compilation error: Invalid end tag.'}),
        ('{{ report.nonexistent_variable.prop }}', {'level': 'error', 'message': "TypeError: Cannot read properties of undefined (reading 'prop')"}),
        ('{{ nonexistent_variable }}', {'level': 'warning', 'message': 'Property "nonexistent_variable" was accessed during render but is not defined on instance.'}),
        ('<ref to="nonexistent" />', {'level': 'warning', 'message': 'Invalid reference'}),
        ('<a href="/files/name/file.pdf">File</a>', {'level': 'warning', 'message': 'Cannot embed uploaded files'}),
        ('<a href="/path/to/relative/url">Relative URL</a>', {'level': 'warning', 'message': 'Link to relative URL'}),
        ('<img src="/assets/name/nonexistent.png" />', {'level': 'warning', 'message': 'Resource not found'}),
        ('<img src="https://example.com/external.png" />', {'level': 'warning', 'message': 'Blocked request to external URL'}),
        (html_load_script('/assets/name/nonexistent.js'), {'level': 'warning', 'message': 'Resource not found' }),
        (html_load_script('https://example.com/external.js'), {'level': 'warning', 'message': 'Blocked request to external URL' }),
        (html_load_script('/assets/name/test.js'), {'level': 'info', 'message': 'Script loaded' }),
        ('<mermaid-diagram>graph TD; A-->[B;</mermaid-diagram>', {'level': 'warning', 'message': 'Mermaid error' }),
    ])
    def test_error_messages(self, template, expected):
        self.project_type.report_template = template
        res = async_to_sync(render_pdf)(project=self.project)
        assert len(res.messages) >= 1
        assert expected in [copy_keys(m.to_dict(), expected.keys()) for m in res.messages]

    def test_markdown_rendering(self):
        assertHTMLEqual(
            self.render_html('<markdown :text="data.md" />', {'md': 'text _with_ **markdown** `code`'}),
            '<div class="markdown"><p>text <em>with</em> <strong>markdown</strong> <code class="code-inline">code</code></p></div>',
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
                    '> blockquote',
                    '> text',
                    '',
                    '',
                    '* [ ] task',
                    '* [x] task',
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
                    '<blockquote><p>blockquote text</p></blockquote>',
                    '<ul class="contains-task-list"><li class="task-list-item"><input type="checkbox" disabled> task</li><li class="task-list-item"><input type="checkbox" checked disabled> task</li>\n</ul>',
                    '<pre class="code-block"><code class="hljs">',
                    '<span class="code-block-line" data-line-number="1">code block content</span>',
                    '<span class="code-block-line" data-line-number="2">    indentation preserved</span>',
                    '<span class="code-block-line" data-line-number="3">&lt;div&gt;&lt;span&gt;HTML&lt;/span&gt; &lt;strong&gt;preserved&lt;/strong&gt;&lt;/div&gt;</span>',
                    '<span class="code-block-line" data-line-number="4">&lt;invalid&gt;HTML</span>',
                    '<span class="code-block-line" data-line-number="5">&lt;!-- comment preserved --&gt;</span>',
                    '</code></pre>',
                    '<p><span>Variable: Report title</span></p>',
                    '</div>',
                ]),
            )

    @pytest.mark.parametrize(("props", "items", "html"), [
        ('', [], '<span></span>'),
        ('', ['a'], '<span>a</span>'),
        ('', ['a', 'b'], '<span>a and b</span>'),
        ('', ['a', 'b', 'c'], '<span>a, b and c</span>'),
        ('comma=";" and="+"', ['a', 'b', 'c'], '<span>a;b+c</span>'),
    ])
    def test_comma_and_join(self, props, items, html):
        actual_html = self.render_html(
            f"""<comma-and-join {props}><template v-for="v, idx in report.field_list" #[idx]>{{{{ v }}}}</template></comma-and-join>""",
            {'report': {'field_list': items}},
        ).replace('<!---->', '')
        assert actual_html == html

    @pytest.mark.parametrize(("template", "expected"), [
        ('<ref to="h1" />' , '<a href="#h1" class="ref ref-heading"><span class="ref-title">H1</span></a>'),
        ('<ref to="h1-numbered" />' , '<a href="#h1-numbered" class="ref ref-heading ref-heading-level1"><span class="ref-title">H1 numbered</span></a>'),
        ('<ref to="h1.1-numbered" />', '<a href="#h1.1-numbered" class="ref ref-heading ref-heading-level2"><span class="ref-title">H1.1 numbered</span></a>'),
        ('<ref to="h1-numbered-appendix" />', '<a href="#h1-numbered-appendix" class="ref ref-heading ref-appendix ref-appendix-level1"><span class="ref-title">H1 appendix</span></a>'),
        ('<ref to="h1.1-numbered-appendix" />', '<a href="#h1.1-numbered-appendix" class="ref ref-heading ref-appendix ref-appendix-level2"><span class="ref-title">H1.1 appendix</span></a>'),
        ('<ref to="h1-numbered">title</ref>', '<a href="#h1-numbered" class="ref"><span class="ref-title">title</span></a>'),
        ('<ref to="fig1" />', '<a href="#fig1" class="ref ref-figure"><span class="ref-title">caption1</span></a>'),
        ('<ref to="fig2-img" />', '<a href="#fig2" class="ref ref-figure"><span class="ref-title">caption2</span></a>'),
        ('<ref to="fig3-caption" />', '<a href="#fig3" class="ref ref-figure"><span class="ref-title">caption3</span></a>'),
        ('<ref to="fig1">title</ref>', '<a href="#fig1" class="ref"><span class="ref-title">title</span></a>'),
        ('<ref to="table1" />', '<a href="#table1" class="ref ref-table"><span class="ref-title">caption1</span></a>'),
        ('<ref to="table2-caption" />', '<a href="#table2" class="ref ref-table"><span class="ref-title">caption2</span></a>'),
        ('<ref to="table1">title</ref>', '<a href="#table1" class="ref"><span class="ref-title">title</span></a>'),
        ('<ref to="other">title</ref>', '<a href="#other" class="ref"><span class="ref-title">title</span></a>'),
    ])
    def test_ref_rendering(self, template, expected):
        html = self.render_html(f"""
            <main>{template}</main>
            <h1 id="h1">H1</h1>
            <h1 id="h1-numbered" class="numbered">H1 numbered</h1>
            <h2 id="h1.1-numbered" class="numbered">H1.1 numbered</h2>
            <div class="appendix">
                <h1 id="h1-numbered-appendix" class="numbered">H1 appendix</h1>
                <h2 id="h1.1-numbered-appendix" class="numbered">H1.1 appendix</h2>
            </div>
            <figure id="fig1"><img id="fig1-img" src="/assets/name/image.png" /><figcaption id="fig1-caption">caption1</figcaption></figure>
            <figure id="fig2"><img id="fig2-img" src="/assets/name/image.png" /><figcaption id="fig2-caption">caption2</figcaption></figure>
            <figure id="fig3"><img id="fig3-img" src="/assets/name/image.png" /><figcaption id="fig3-caption">caption3</figcaption></figure>
            <table id="table1"><caption id="table1-caption">caption1</caption></table>
            <table id="table2"><caption id="table2-caption">caption2</caption></table>
            <div id="other">other</div>
        """)
        actual = self.extract_html_part(html, '<main>', '</main>')[6:-7]
        assertHTMLEqual(actual, expected)

    @pytest.mark.parametrize("slotDataSyntax", [
        'tocItems',
        '{ items: tocItems }',
    ])
    def test_toc_rendering(self, slotDataSyntax):
        html = self.render_html(f"""
        <table-of-contents v-slot="{slotDataSyntax}">
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
        """,
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

    @pytest.mark.parametrize("slotDataSyntax", [
        'figures',
        '{ items: figures }',
    ])
    def test_lof_rendering(self, slotDataSyntax):
        html = self.render_html(f"""
        <list-of-figures v-slot="{slotDataSyntax}">
            <section v-if="figures">
                <h1 id="lof" class="in-lof">List of Figures</h1>
                <ul>
                    <li v-for="figure in figures">
                        <ref :to="figure.id" />
                    </li>
                </ul>
            </section>
        </list-of-figures>
        <figure id="fig1"><img src="/assets/name/image.png" /><figcaption>caption1</figcaption></figure>
        <figure id="fig2"><img src="/assets/name/image.png" /><figcaption>caption2</figcaption></figure>
        <figure id="fig3"><img src="/assets/name/image.png" /><figcaption>caption3</figcaption></figure>
        """)
        assertHTMLEqual(self.extract_html_part(html, '<ul>', '</ul>'), """
        <ul>
            <li><a href="#fig1" class="ref ref-figure"><span class="ref-title">caption1</span></a></li>
            <li><a href="#fig2" class="ref ref-figure"><span class="ref-title">caption2</span></a></li>
            <li><a href="#fig3" class="ref ref-figure"><span class="ref-title">caption3</span></a></li>
        </ul>
        """)

    @pytest.mark.parametrize("slotDataSyntax", [
        'tables',
        '{ items: tables }',
    ])
    def test_lot_rendering(self, slotDataSyntax):
        html = self.render_html(f"""
        <list-of-tables v-slot="{slotDataSyntax}">
            <section v-if="tables">
                <h1 id="lot" class="in-lot">List of Tables</h1>
                <ul>
                    <li v-for="table in tables">
                        <ref :to="table.id" />
                    </li>
                </ul>
            </section>
        </list-of-tables>
        <table id="table1"><caption>caption1</caption></table>
        <table id="table2"><caption>caption2</caption></table>
        """)
        assertHTMLEqual(self.extract_html_part(html, '<ul>', '</ul>'), """
        <ul>
            <li><a href="#table1" class="ref ref-table"><span class="ref-title">caption1</span></a></li>
            <li><a href="#table2" class="ref ref-table"><span class="ref-title">caption2</span></a></li>
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
            options: {scales: {y: {beginAtZero: true, ticks: {precision: 0}}}, plugins: {legend: {display: false}}},
            plugins: [ chartjsPlugins.DataLabels ],
        }" />""")
        assert re.fullmatch(r'^\s*<img src="data:image/png;base64,[a-zA-Z0-9+/=]+" alt="" style="width: 15cm; height: 10cm;">\s*$', html)

    def test_mermaid_rendering(self):
        html = self.render_html("""
        <mermaid-diagram>
            graph TD
                A --> B;
        </mermaid-diagram>
        """)
        assert re.fullmatch(r'^\s*<div class="mermaid-diagram">\s*<img src="data:image/png;base64,[a-zA-Z0-9+/=]+" alt="">\s*</div>\s*$', html)

    @pytest.mark.parametrize(("password", "encrypted"), [
        ('password', True),
        ('', False),
    ])
    def test_pdf_encryption(self, password, encrypted):
        pdf_data = async_to_sync(render_pdf)(project=self.project, password=password).pdf
        with pikepdf.Pdf.open(io.BytesIO(pdf_data), password=password) as pdf:
            assert pdf.is_encrypted == encrypted

    def test_render_md2html(self):
        md = '# headline\ntext _with_ **markdown** `code`'
        html = '<h1>headline</h1>\n<p>text <em>with</em> <strong>markdown</strong> <code class="code-inline">code</code></p>'

        section = update(self.project.sections.get(section_id='other'), data={'field_markdown': md})
        finding = update(self.project.findings.first(), data={'field_markdown': md})

        res = async_to_sync(render_project_markdown_fields_to_html)(project=self.project, request=None)

        section_data = next(filter(lambda s: s['id'] == section.section_id, res['result']['sections']))
        assertHTMLEqual(section_data['data']['field_markdown'], html)
        finding_data = next(filter(lambda f: f['id'] == str(finding.finding_id), res['result']['findings']))
        assertHTMLEqual(finding_data['data']['field_markdown'], html)

