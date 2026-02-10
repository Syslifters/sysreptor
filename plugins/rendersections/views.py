from asgiref.sync import sync_to_async
from django.db.models import Prefetch, aprefetch_related_objects
from lxml import etree
from rest_framework import status
from rest_framework.response import Response
from rest_framework.settings import api_settings
from sysreptor.pentests.models import PentestFinding
from sysreptor.pentests.rendering.entry import render_pdf, render_pdf_task
from sysreptor.pentests.views import ProjectSubresourceMixin
from sysreptor.utils.api import GenericAPIViewAsync

from .serializers import RenderSectionsSerializer

RENDERSECTIONS_ATTRIBUTE = 'data-sysreptor-rendersections'
RENDERSECTIONS_SELECTOR_ALWAYS = f"@{RENDERSECTIONS_ATTRIBUTE}='always'"
RENDERSECTIONS_SELECTOR_CHOOSABLE = f"@{RENDERSECTIONS_ATTRIBUTE}='choosable'"
RENDERSECTIONS_SELECTOR_RELATED = f"@{RENDERSECTIONS_ATTRIBUTE}='related'"

RENDERSECTIONS_RELATEDIDS_ATTRIBUTE = 'data-sysreptor-rendersections-relatedids'

ALWAYS_SELECTOR = f"({RENDERSECTIONS_SELECTOR_ALWAYS})"

CHOOSABLE_SELECTOR = f"({RENDERSECTIONS_SELECTOR_CHOOSABLE} and @id)"
CHOOSABLE_XPATH = f"//*[{CHOOSABLE_SELECTOR}]"

RELATED_SELECTOR = f"({RENDERSECTIONS_SELECTOR_RELATED} and @{RENDERSECTIONS_RELATEDIDS_ATTRIBUTE})"
RELATED_XPATH =   f"//*[({RELATED_SELECTOR})]"

FILTERING_XPATH = f"//*[({ALWAYS_SELECTOR} or {CHOOSABLE_SELECTOR} or {RELATED_SELECTOR})]"


class RenderSectionsView(ProjectSubresourceMixin, GenericAPIViewAsync):
    serializer_class = RenderSectionsSerializer
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES

    def filter_element(self, elem, section_ids, include_parent=False):
        """
        Recursively filter element and its children.
        
        Args:
            elem: The element to filter
            section_ids: List of selected section IDs
            include_parent: True if parent was explicitly included
            
        Returns:
            Filtered element or None if it should be excluded
        """
        if not isinstance(elem, etree.Element) or not isinstance(elem.tag, str):
            # Ignore special elements e.g. comments
            return None

        mode = elem.get(RENDERSECTIONS_ATTRIBUTE)
        explicitly_included = False
        
        if mode == "always":
            explicitly_included = True
        elif mode == "choosable":
            elem_id = elem.get("id")
            if elem_id and elem_id in section_ids:
                explicitly_included = True
            else:
                return None  # Explicitly excluded
        elif mode == 'related':
            related_ids = elem.get(RENDERSECTIONS_RELATEDIDS_ATTRIBUTE, '')
            if related_ids and set(related_ids.split(",")) & set(section_ids):
                explicitly_included = True
        
        # Determine if we should force include all children
        include_children = explicitly_included or include_parent
        
        # Copy element
        new_elem = etree.Element(elem.tag, attrib=elem.attrib, nsmap=elem.nsmap)
        if include_children:
            if elem.text:
                new_elem.text = elem.text
        if include_parent:
            if elem.prefix:
                new_elem.prefix = elem.prefix
            if elem.tail:
                new_elem.tail = elem.tail
        
        # Recursively process children
        has_included_children = False
        for child in elem:
            filtered_child = self.filter_element(child, section_ids, include_parent=include_children)
            if filtered_child is not None:
                new_elem.append(filtered_child)
                has_included_children = True
        
        # Include element if:
        # 1. Explicitly included, OR
        # 2. Parent forced inclusion (and not explicitly excluded), OR  
        # 3. Has any included children (propagate up)
        should_keep = explicitly_included or include_parent or has_included_children
        return new_elem if should_keep else None

    @sync_to_async()
    def post_process_html(self, html, section_ids):
        html_tree = etree.HTML(html)
        old_body = html_tree.find("body/div")
        new_body = etree.Element("div")

        # Recursively filter each top-level child of body
        for child in old_body:
            filtered_child = self.filter_element(child, section_ids, include_parent=False)
            if filtered_child is not None:
                new_body.append(filtered_child)
        
        parent = old_body.getparent()
        parent.remove(old_body)
        parent.append(new_body)

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
        else:
            return Response(data=res.to_dict(), status=status.HTTP_400_BAD_REQUEST)
