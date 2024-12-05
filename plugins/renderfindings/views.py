from asgiref.sync import sync_to_async
from django.db.models import Prefetch, aprefetch_related_objects
from lxml import etree
from reportcreator_api.pentests.models import PentestFinding
from reportcreator_api.pentests.views import ProjectSubresourceMixin
from reportcreator_api.tasks.rendering.entry import render_pdf, render_pdf_task
from reportcreator_api.utils.api import GenericAPIViewAsync
from rest_framework.response import Response

from .serializers import RenderFindingsSerializer


class RenderFindingPdfView(ProjectSubresourceMixin, GenericAPIViewAsync):
    serializer_class = RenderFindingsSerializer

    def to_xpath(self, selectors):
        out = []
        for s in selectors:
            try:
                out.append(etree.XPath(s))
            except Exception:
                pass
            try:
                out.append(etree.XPath(f'.//*[{s}]'))
            except Exception:
                pass
        return out

    @sync_to_async()
    def post_process_html(self, html, findings):
        html_tree = etree.HTML(html)

        # Get top-level elements
        html_toplevel = html_tree.find('body/div').getchildren()
        if len(html_toplevel) == 1 and html_toplevel[0].tag == 'div' and not html_toplevel[0].attrib:
            # Handle top-level wrapper
            html_toplevel = html_toplevel[0].getchildren()
        
        include_selectors = self.to_xpath([
            # Explicitely included elements
            '@data-sysreptor-renderfindingpdf="include"',
            # Include page headers and footers by default
            '@data-sysreptor-generated="page-header"', '@id="header"',
            '@data-sysreptor-generated="page-footer"', '@id="footer"',
        ] + [f'@id="{f.finding_id}"' for f in findings])
        exclude_selectors = self.to_xpath([
            # Explicitely excluded elements
            '@data-sysreptor-renderfindingpdf="exclude"',
        ])
        for elem in list(html_toplevel):
            # Only include top-level elements matching include_selectors
            for selector in include_selectors:
                try:
                    if selector(elem):
                        break
                except Exception:
                    pass
            else:
                html_toplevel.remove(elem)
                elem.getparent().remove(elem)
                continue
                
            # Remove all (sub)-elements matching exclude_selectors
            for selector in exclude_selectors:
                try:
                    selector_res = selector(elem)
                    if isinstance(selector_res, list):
                        for e in selector_res:
                            e.getparent().remove(e)
                    elif selector_res:
                        elem.getparent().remove(elem)
                except Exception:
                    pass
        
        return etree.tostring(html_tree, method="html", pretty_print=True)

    async def post(self, request, *args, **kwargs):
        serializer = await self.aget_valid_serializer(data=request.data)
        finding_ids = serializer.validated_data['finding_ids']

        # Render findings to HTML
        project = self.get_project()
        await aprefetch_related_objects([project], Prefetch('findings', PentestFinding.objects.filter(finding_id__in=finding_ids)), 'sections')
        res = await render_pdf(project=project, output='html')

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

