import json

from decouple import config
from lxml import etree
from reportcreator_api.conf.plugins import PluginConfig


class RenderFindingPdfPluginConfig(PluginConfig):
    plugin_id = '62d0f5ae-5c07-47c6-9203-a9d9c3dbffb2'

    # TODO: do we need settings?
    #       instead: annotate HTML elements in the design with data-sysreptor-renderfindingpdf="include|exclude"
    settings = {
        'PLUGIN_RENDERFINDINGPDF_INCLUDE_ELEMENTS': [
            '@data-sysreptor-generated="page-header"', '@id="header"',
            '@data-sysreptor-generated="page-footer"', '@id="footer"',
            '@data-sysreptor-renderfindingpdf="include"',
        ],
        'PLUGIN_RENDERFINDINGPDF_EXCLUDE_ELEMENTS': [
            '@data-sysreptor-renderfindingpdf="exclude"',
        ],
    }

    def ready(self) -> None:
        self.settings = self.load_settings()

    def load_settings(self):
        return (
            self.load_selectors('PLUGIN_RENDERFINDINGPDF_INCLUDE_ELEMENTS') |
            self.load_selectors('PLUGIN_RENDERFINDINGPDF_EXCLUDE_ELEMENTS')
        )
    
    def load_selectors(self, name):
        value = config(name, cast=json.loads, default=json.dumps(self.settings.get(name, [])))
        if not isinstance(value, list):
            raise ValueError(f"Setting '{name}' must be a JSON list")
        for v in value:
            try:
                etree.XPath(v)
            except Exception:
                raise ValueError(f"Setting '{name}' item '{v}' is not a valid XPath selector")
        return {name: value}



# TODO: render single finding pdf
# * [x] API
#   * [x] render_findings_pdf:
#       * render findings to HTML
#       * postprocess HTML: remove all HTML tags except id="finding_id", selectors in allowlist, parent element
#       * render HTML to PDF
#   * [x] modify render function: allow rendering HTML+CSS to PDF
#   * [x] API endpoint: async
# * [ ] frontend
#   * [ ] per-project menu entry
#   * [ ] select one or multiple findings
#   * [ ] PDF preview
#   * [ ] move PdfPreview to nuxt-base-layer
# * [ ] other
#   * [ ] reuse plugin to render finding summary ???
# * [ ] tests
#   * [ ] test api + permissions
#   * [x] test render HTML + HTML stripping => set pytest-xdist group
#   * [ ] test with designs: HTB, OSCP, Syslifters, customer designs
# * [ ] documentation
#   * [ ] problem: title page, executive summary, other report data included in PDF
#       * design's HTML templates would need to explicitly support render single findings (e.g. pass a variable to the template for conditional rendering)
#       * solution: post-process the HTML to remove all elements except the finding element (and headers, footers, etc.), then render PDF
#   * [ ] PLUGIN_RENDERFINDINGPDF_INCLUDE_ELEMENTS='["...", "..."]' => JSON list of XPath selectors of HTML elements to include (headers, footers, etc.)
#   * [ ] PLUGIN_RENDERFINDINGPDF_REMOVE_ELEMENTS='["...", "..."]' => JSON list of XPath selectors of HTML elements to remove
#   * [ ] data-sysreptor-renderfindingpdf="include|exclude"
#   * [ ] might need to update the design's CSS: named pages instead of "@page:first/last"
#   * [ ] design: has to set the finding ID as an ID attribute on the finding element (e.g. <div v-for="finding in findings" :id="finding.id">)
#   * [ ] limitations
#       * different heading, figure, table, etc. numbers for findings (counters start at 1 for first finding in PDF)
#       * references to other findings or sections do not work (if they are not included in the PDF)
 