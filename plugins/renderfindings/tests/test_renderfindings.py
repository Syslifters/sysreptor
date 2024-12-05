
from unittest import mock

import pytest
from django.urls import reverse
from lxml import etree
from pytest_django.asserts import assertHTMLEqual
from reportcreator_api.tasks.rendering.render import render_pdf_impl
from reportcreator_api.tasks.rendering.render_utils import RenderStageResult
from reportcreator_api.tests.mock import (
    api_client,
    create_finding,
    create_project,
    create_project_type,
    create_user,
)

from ..app import RenderFindingsPluginConfig

URL_NAMESPACE = RenderFindingsPluginConfig.label


@pytest.mark.xdist_group('rendering')
@pytest.mark.django_db()
class TestRenderSingleFindingPdf:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user()
        self.client = api_client(self.user)
        self.report_template = '''
            <div data-sysreptor-generated="page-header">header</div>
            <div data-sysreptor-generated="page-footer">footer</div>
            <section>
                <h1>Findings</h1>
                <div v-for="finding in findings"><h2 :id="finding.id">{{ finding.title }}</h2></div>
            </section>
        '''
        self.project_type = create_project_type(report_template=self.report_template)
        self.project = create_project(project_type=self.project_type, members=[self.user], findings_kwargs=[])
        self.finding1 = create_finding(project=self.project, data={'title': 'Finding 1'}, finding_id="11111111-1111-1111-1111-111111111111")
        self.finding2 = create_finding(project=self.project, data={'title': 'Finding 2'})
        self.finding3 = create_finding(project=self.project, data={'title': 'Finding 3'})

    def render_html(self, findings, template=None):
        self.project_type.report_template = template or self.report_template
        self.project_type.save()

        async def render_only_html(output, **kwargs):
            return await render_pdf_impl(
                **kwargs,
                output='html',
            )

        with mock.patch('reportcreator_api.tasks.rendering.render.render_pdf_impl', render_only_html):
            res = self.client.post(reverse(f'{URL_NAMESPACE}:renderfindings', kwargs={'project_pk': self.project.id}), data={
                'finding_ids': [f.finding_id for f in findings]
            })
            assert res.status_code == 200
            assert not res.data['messages']
            html = RenderStageResult.from_dict(res.data).pdf.decode()
            return etree.tostring(etree.HTML(html).find('body/div')).decode()[5:-6]
    
    def test_render_pdf(self):
        res = self.client.post(reverse(f'{URL_NAMESPACE}:renderfindings', kwargs={'project_pk': self.project.id}), data={
            'finding_ids': [self.finding1.finding_id]
        })
        assert res.status_code == 200
        assert res.data['pdf'] is not None
        assert not res.data['messages']

    def test_render_single_finding(self):
        html = self.render_html(findings=[self.finding1])
        assert self.finding1.title in html
        assert self.finding2.title not in html
        assert self.finding3.title not in html
    
    def test_render_multiple_findings(self):
        html = self.render_html(findings=[self.finding1, self.finding2])
        assert self.finding1.title in html
        assert self.finding2.title in html
        assert self.finding3.title not in html

    @pytest.mark.parametrize(['template', 'expected'], [
        ('<div id="header">include</div><div>exclude</div>', '<div id="header">include</div>'),
        ('<div id="footer">include</div><div>exclude</div>', '<div id="footer">include</div>'),
        ('<div data-sysreptor-generated="page-header">include</div><div>exclude</div>', '<div data-sysreptor-generated="page-header">include</div>'),
        ('<div data-sysreptor-generated="page-footer">include</div><div>exclude</div>', '<div data-sysreptor-generated="page-footer">include</div>'),
        ('<div data-sysreptor-renderfindings="include">include</div><div>exclude</div>', '<div data-sysreptor-renderfindings="include">include</div>'),
        ('<div data-sysreptor-renderfindings="include">include<div v-if="!data.isPluginRenderFindings">exclude</div></div>', '<div data-sysreptor-renderfindings="include">include</div>'),
        ('<div v-if="!data.isPluginRenderFindings">exclude<div data-sysreptor-renderfindings="include">include</div></div>', ''),
        ('<div id="summary">summary</div><div v-for="finding in findings" :id="finding.id">finding</div>', '<div id="11111111-1111-1111-1111-111111111111">finding</div>'),
        ('<div id="summary">summary</div><section class="findings-list"><h1>Findings</h1><div v-for="finding in findings" :id="finding.id">finding</div></section>', '<section class="findings-list"><h1>Findings</h1><div id="11111111-1111-1111-1111-111111111111">finding</div></section>'),
        ('<div v-if="data.isPluginRenderFindings">exclude</div><div v-else>exclude</div>', ''),
        ('<div v-if="data.isPluginRenderFindings" data-sysreptor-renderfindings="include">include</div><div v-else>exclude</div>', '<div data-sysreptor-renderfindings="include">include</div>'),
    ])
    def test_html_postprocess(self, template, expected):
        html = self.render_html(findings=[self.finding1], template=template)
        assertHTMLEqual(html, expected)
