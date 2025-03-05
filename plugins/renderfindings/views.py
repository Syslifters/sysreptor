from asgiref.sync import sync_to_async
from django.db.models import Prefetch, aprefetch_related_objects
from lxml import etree
from reportcreator_api.pentests.models import PentestFinding
from reportcreator_api.pentests.views import ProjectSubresourceMixin
from reportcreator_api.tasks.rendering.entry import render_pdf, render_pdf_task
from reportcreator_api.utils.api import GenericAPIViewAsync
from rest_framework.response import Response
from rest_framework.settings import api_settings

from .serializers import RenderFindingsSerializer


class RenderFindingsView(ProjectSubresourceMixin, GenericAPIViewAsync):
    serializer_class = RenderFindingsSerializer
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES

    @sync_to_async()
    def post_process_html(self, html, findings):
        html_tree = etree.HTML(html)
        # Get top-level sections
        html_toplevel = html_tree.find('body/div').getchildren()

        include_selectors = [
            # Explicitely included elements
            etree.XPath('.//@data-sysreptor-renderfindings="include"'),
            # Include page headers and footers by default
            etree.XPath('.//@data-sysreptor-generated="page-header"'), etree.XPath('.//@id="header"'),
            etree.XPath('.//@data-sysreptor-generated="page-footer"'), etree.XPath('.//@id="footer"'),
        ] + [
            # Include findings
            etree.XPath(f'.//@id="{f.finding_id}"') for f in findings
        ]
        for elem in list(html_toplevel):
            # Only include top-level sections matching include_selectors
            for selector in include_selectors:
                try:
                    if selector(elem):
                        break
                except (ValueError, etree.XPathEvalError):
                    pass
            else:
                html_toplevel.remove(elem)
                elem.getparent().remove(elem)

        return etree.tostring(html_tree, method="html", pretty_print=True)

    async def post(self, request, *args, **kwargs):
        project = await sync_to_async(self.get_project)()

        serializer = await self.aget_valid_serializer(data=request.data)
        finding_ids = serializer.validated_data['finding_ids']

        # Render findings to HTML
        await aprefetch_related_objects([project], Prefetch('findings', PentestFinding.objects.filter(finding_id__in=finding_ids)), 'sections')
        res = await render_pdf(project=project, additonal_data={'isPluginRenderFindings': True}, output='html')

        # Post-process HTML to remove unwanted elements
        if res.pdf:
            with res.add_timing('other'):
                res.pdf = await self.post_process_html(res.pdf.decode(), project.findings.all())

        # Render HTML to PDF
        if res.pdf:
            res |= await render_pdf_task(
                project=project,
                project_type=project.project_type,
                data={},
                report_template='',
                report_styles=project.project_type.report_styles,
                html=res.pdf.decode())

        return Response(data=res.to_dict())

