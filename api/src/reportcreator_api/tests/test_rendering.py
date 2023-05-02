import pytest
import io
import re
import pikepdf
from asgiref.sync import async_to_sync
from unittest import mock
from pytest_django.asserts import assertHTMLEqual
from django.test import override_settings

from reportcreator_api.tests.mock import create_project_type, create_project, create_user, create_finding
from reportcreator_api.tasks.rendering.entry import render_pdf, PdfRenderingError
from reportcreator_api.tasks.rendering.render import render_to_html
from reportcreator_api.utils.utils import merge


@pytest.mark.django_db
class TestHtmlRendering:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user()
        self.project_type = create_project_type()
        self.project = create_project(project_type=self.project_type, members=[self.user], findings_kwargs=[])
        self.finding = create_finding(project=self.project)

        with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
            yield
    
    def render_html(self, template, additional_data={}):
        def render_only_html(data, language, **kwargs):
            html, msgs = render_to_html(template=template, data=merge(data, additional_data), language=language)
            return html.encode() if html else None, msgs
        
        with mock.patch('reportcreator_api.tasks.rendering.render.render_pdf', render_only_html):
            html = async_to_sync(render_pdf)(self.project).decode()
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
        ('{{ data.pentesters[0].name }}', lambda self: self.user.name),
        ('{{ data.pentesters[0].email }}', lambda self: self.user.email),
        ('<template v-for="r in data.pentesters[0].roles">{{ r }}</template>', lambda self: ''.join(self.project.members.all()[0].roles)),
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

    @pytest.mark.parametrize('template', [
        '<markdown></p>',
        '{{ report.nonexistent_variable.prop }}'
    ])
    def test_template_error(self, template):
        with pytest.raises(PdfRenderingError):
            self.project_type.report_template = template
            async_to_sync(render_pdf)(project=self.project)

    def test_markdown_rendering(self):
        assertHTMLEqual(
            self.render_html('<markdown :text="data.md" />', {'md': 'text _with_ **markdown** `code`'}), 
            '<div class="markdown"><p>text <em>with</em> <strong>markdown</strong> <code class="code-inline">code</code></p></div>'
        )

    def test_toc_rendering(self):
        html = self.render_html("""
        <table-of-contents v-slot="tocItems">
            <section v-if="tocItems">
                <h1 class="in-toc" id="toc">Table of Contents</h1>
                <ul class="toc">
                    <template v-for="item in tocItems">
                        <li :class="['toc-level-' + item.level, (item.attrs.class || '').split(' ').includes('numbered') ? 'numbered' : '', (item.attrs.class || '').split(' ').includes('numbered-appendix') ? 'numbered-appendix' : '']">
                            <a :href="item.href">{{ item.title }}</a>
                        </li>
                    </template>
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
        <h1 class="in-toc numbered-appendix" id="a">Appendix</h1>
        <h2 class="in-toc numbered-appendix" id="a.1">A.1</h2>
        """)
        assertHTMLEqual(self.extract_html_part(html, '<ul class="toc">', '</ul>'), """
        <ul class="toc">
            <li class="toc-level-1"><a href="#toc">Table of Contents</a></li>
            <li class="toc-level-1 numbered"><a href="#h1">H1</a></li>
            <li class="toc-level-2 numbered"><a href="#h1.1">H1.1</a></li>
            <li class="toc-level-3 numbered"><a href="#h1.1.1">H1.1.1</a></li>
            <li class="toc-level-2"><a href="#h1.2">H1.2</a></li>
            <li class="toc-level-2 numbered"><a href="#h1.3">H1.3</a></li>
            <li class="toc-level-1 numbered"><a href="#h2">H2</a></li>
            <li class="toc-level-2 numbered"><a href="#h2.1">H2.1</a></li>
            <li class="toc-level-1 numbered-appendix"><a href="#a">Appendix</a></li>
            <li class="toc-level-2 numbered-appendix"><a href="#a.1">A.1</a></li>
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
        pdf_data = async_to_sync(render_pdf)(project=self.project, password=password)
        with pikepdf.Pdf.open(io.BytesIO(pdf_data), password=password) as pdf:
            assert pdf.is_encrypted == encrypted

