from xml.etree.ElementPath import xpath_tokenizer
from asgiref.sync import sync_to_async
from django.db.models import Prefetch, aprefetch_related_objects
from lxml import etree
from rest_framework.response import Response
from rest_framework.settings import api_settings
from sysreptor.pentests.models import PentestFinding
from sysreptor.pentests.rendering.entry import render_pdf, render_pdf_task
from sysreptor.pentests.views import ProjectSubresourceMixin
from sysreptor.utils.api import GenericAPIViewAsync

from .serializers import RenderSectionsSerializer


RENDERSECTIONS_ATTRIBUTE = 'data-sysreptor-rendersections'
RENDERSECTIONS_SELECTOR_CHOOSABLE = f"@{RENDERSECTIONS_ATTRIBUTE}='choosable'"
RENDERSECTIONS_SELECTOR_RELATED = f"@{RENDERSECTIONS_ATTRIBUTE}='related'"

RENDERSECTIONS_RELATEDIDS_ATTRIBUTE = 'data-sysreptor-rendersections-relatedids'

CHOOSABLE_SELECTOR = f"({RENDERSECTIONS_SELECTOR_CHOOSABLE} and @id)"
CHOOSABLE_XPATH = f"//*[{CHOOSABLE_SELECTOR}]"

RELATED_SELECTOR = f"({RENDERSECTIONS_SELECTOR_RELATED} and @{RENDERSECTIONS_RELATEDIDS_ATTRIBUTE})"
RELATED_XPATH =   f"//*[({RELATED_SELECTOR})]"

FILTERING_XPATH = f"//*[({CHOOSABLE_SELECTOR} or {RELATED_SELECTOR})]"


class RenderSectionsView(ProjectSubresourceMixin, GenericAPIViewAsync):
    serializer_class = RenderSectionsSerializer
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES

    @sync_to_async()
    def post_process_html(self, html, section_ids):
        html_tree = etree.HTML(html)

        for elem in html_tree.xpath(FILTERING_XPATH):
            keep = False

            if elem.get(RENDERSECTIONS_ATTRIBUTE) == "choosable" \
                and elem.get("id") in section_ids:
                    keep = True

            elif elem.get(RENDERSECTIONS_ATTRIBUTE) == 'related' \
                and set(elem.get(RENDERSECTIONS_RELATEDIDS_ATTRIBUTE).split(",")) & set(section_ids):
                    keep = True

            if not keep:
                elem.getparent().remove(elem)

        return etree.tostring(html_tree, method="html", pretty_print=True)

    async def post(self, request, *args, **kwargs):
        project = await sync_to_async(self.get_project)()

        serializer = await self.aget_valid_serializer(data=request.data)
        section_ids = serializer.validated_data['sections']

        # Render report to HTML
        await aprefetch_related_objects([project], Prefetch('findings', PentestFinding.objects.filter(project=project)), 'sections')
        res = await render_pdf(project=project, additional_data={'isPluginRenderFindings': True}, output='html')

        # Post-process HTML to remove unwanted elements
        if res.pdf:
            with res.add_timing('other'):
                res.pdf = await self.post_process_html(res.pdf.decode(), section_ids)

        # Render HTML to PDF
        if res.pdf:
            res |= await render_pdf_task(
                project=project,
                project_type=project.project_type,
                data={},
                report_template='',
                report_styles=project.project_type.report_styles,
                html=res.pdf.decode(),
                password=serializer.validated_data.get("pdf_password", None),
            )

        return Response(data=res.to_dict())


class GetSectionsView(ProjectSubresourceMixin, GenericAPIViewAsync):
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES

    @sync_to_async()
    def get_choosable_sections(self, html):
        html_tree = etree.HTML(html)

        sections = []
        for node in html_tree.xpath(CHOOSABLE_XPATH):
            node_id = node.get('id')
            name = node.get('data-sysreptor-rendersections-name', node_id)
            sections.append({"id": node_id, "name": name})

        return sections

    async def get(self, request, *args, **kwargs):
        project = await sync_to_async(self.get_project)()

        await aprefetch_related_objects([project], Prefetch('findings', PentestFinding.objects.filter(project=project)), 'sections')
        res = await render_pdf(project=project, additional_data={'isPluginRenderFindings': True}, output='html')

        if res.pdf:
            with res.add_timing('other'):
                choosable_sections = await self.get_choosable_sections(res.pdf.decode())
                return Response(data=choosable_sections)

        return Response(data=res.to_dict())
