
from unittest import mock

import pytest
from django.urls import reverse
from lxml import etree
from pytest_django.asserts import assertHTMLEqual
from sysreptor.pentests.rendering.render import render_pdf_impl
from sysreptor.pentests.rendering.render_utils import RenderStageResult
from sysreptor.tests.mock import (
    api_client,
    create_finding,
    create_project,
    create_project_type,
    create_user,
)

from ..apps import RenderSectionsPluginConfig

URL_NAMESPACE = RenderSectionsPluginConfig.label


@pytest.mark.xdist_group('rendering')
@pytest.mark.django_db()
class TestRenderSingleSectionPdf:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user()
        self.client = api_client(self.user)
        self.report_template = '''
            <div data-sysreptor-generated="page-header">header</div>
            <div data-sysreptor-generated="page-footer">footer</div>
            <section>
                <h1>Findings</h1>
                <div v-for="finding in findings"
                    :id="finding.id"
                    data-sysreptor-rendersections="choosable"
                    :data-sysreptor-rendersections-name="finding.title"
                >
                    <h2>{{ finding.title }}</h2>
                </div>
            </section>
        '''
        self.project_type = create_project_type(report_template=self.report_template)
        self.project = create_project(project_type=self.project_type, members=[self.user], findings_kwargs=[])
        self.finding1 = create_finding(project=self.project, data={'title': 'Finding 1'}, finding_id="11111111-1111-1111-1111-111111111111")
        self.finding2 = create_finding(project=self.project, data={'title': 'Finding 2'})
        self.finding3 = create_finding(project=self.project, data={'title': 'Finding 3'})

    def render_html(self, sections, template=None):
        self.project_type.report_template = template or self.report_template
        self.project_type.save()

        async def render_only_html(output, **kwargs):
            return await render_pdf_impl(
                **kwargs,
                output='html',
            )

        with mock.patch('sysreptor.pentests.rendering.render.render_pdf_impl', render_only_html):
            res = self.client.post(reverse(f'{URL_NAMESPACE}:rendersections', kwargs={'project_pk': self.project.id}), data={
                'sections': sections,
            })
            assert res.status_code == 200
            assert not res.data['messages']
            html = RenderStageResult.from_dict(res.data).pdf.decode()
            return etree.tostring(etree.HTML(html).find('body/div')).decode()[5:-6]

    def test_render_pdf(self):
        res = self.client.post(reverse(f'{URL_NAMESPACE}:rendersections', kwargs={'project_pk': self.project.id}), data={
            'sections': [self.finding1.finding_id],
        })
        assert res.status_code == 200
        assert res.data['pdf'] is not None
        assert not res.data['messages']

    def test_render_single_section(self):
        html = self.render_html(sections=[self.finding1.finding_id])
        assert self.finding1.title in html
        assert self.finding2.title not in html
        assert self.finding3.title not in html

    def test_render_multiple_sections(self):
        html = self.render_html(sections=[self.finding1.finding_id, self.finding2.finding_id])
        assert self.finding1.title in html
        assert self.finding2.title in html
        assert self.finding3.title not in html

    @pytest.mark.parametrize(('template', 'expected'), [
        ('<div>include</div><div id="excluded" data-sysreptor-rendersections="choosable">exclude</div>', '<div>include</div>'),
        ('<div>include<div v-if="!data.isPluginRenderFindings">exclude</div></div>', '<div>include</div>'),
        ('<div v-if="!data.isPluginRenderFindings">exclude<div>include</div></div>', ''),
        ('<div id="summary">summary</div><div v-for="finding in findings" :id="finding.id" data-sysreptor-rendersections="choosable">finding</div>', '<div id="summary">summary</div><div id="11111111-1111-1111-1111-111111111111" data-sysreptor-rendersections="choosable">finding</div>'),
        ('<div id="summary">summary</div><div v-for="finding in findings" :id="finding.id" data-sysreptor-rendersections="choosable" :data-sysreptor-rendersections-name="finding.title">finding</div>', '<div id="summary">summary</div><div id="11111111-1111-1111-1111-111111111111" data-sysreptor-rendersections="choosable" data-sysreptor-rendersections-name="Finding 1">finding</div>'),
        ('<div id="summary">summary</div><section class="findings-list"><h1>Findings</h1><div v-for="finding in findings" :id="finding.id" data-sysreptor-rendersections="choosable">finding</div></section>', '<div id="summary">summary</div><section class="findings-list"><h1>Findings</h1><div id="11111111-1111-1111-1111-111111111111" data-sysreptor-rendersections="choosable">finding</div></section>'),
        ('<div id="summary">summary</div><div v-for="finding in findings" :id="finding.id" data-sysreptor-rendersections="choosable">finding</div><div data-sysreptor-rendersections="related" data-sysreptor-rendersections-relatedids="11111111-1111-1111-1111-111111111111">related</div>', '<div id="summary">summary</div><div id="11111111-1111-1111-1111-111111111111" data-sysreptor-rendersections="choosable">finding</div><div data-sysreptor-rendersections="related" data-sysreptor-rendersections-relatedids="11111111-1111-1111-1111-111111111111">related</div>'),
        ('<div id="summary">summary</div><div v-for="finding in findings" :id="finding.id" data-sysreptor-rendersections="choosable">finding</div><div data-sysreptor-rendersections="related" data-sysreptor-rendersections-name="Related" data-sysreptor-rendersections-relatedids="non-existing">related</div>', '<div id="summary">summary</div><div id="11111111-1111-1111-1111-111111111111" data-sysreptor-rendersections="choosable">finding</div>'),
    ])
    def test_html_postprocess(self, template, expected):
        html = self.render_html(sections=[self.finding1.finding_id], template=template)
        assertHTMLEqual(html, expected)


@pytest.mark.django_db()
class TestPluginApiPermissions:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user()
        self.user_other = create_user()
        self.project = create_project(members=[self.user])

    def test_permissions(self):
        url = reverse(f'{URL_NAMESPACE}:rendersections', kwargs={'project_pk': self.project.id})
        assert api_client(self.user).post(url, data={}).status_code == 400  # Allowed, but no findings selected
        assert api_client(self.user_other).post(url, data={}).status_code in [403, 404]  # Forbidden
