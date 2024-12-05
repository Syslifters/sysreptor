from reportcreator_api.conf.plugins import PluginConfig


class RenderFindingsPluginConfig(PluginConfig):
    plugin_id = '62d0f5ae-5c07-47c6-9203-a9d9c3dbffb2'
    professional_only = True


# TODO: render single finding pdf
# * [x] API
#   * [x] render_findings_pdf:
#       * render findings to HTML
#       * postprocess HTML: remove all HTML tags except id="finding_id", selectors in allowlist, parent element
#       * render HTML to PDF
#   * [x] modify render function: allow rendering HTML+CSS to PDF
#   * [x] API endpoint: async
# * [x] frontend
#   * [x] per-project menu entry
#   * [x] select one or multiple findings
#   * [x] PDF preview
#   * [x] move PdfPreview to nuxt-base-layer
# * [ ] tests
#   * [ ] test api + permissions
#   * [x] test render HTML + HTML stripping => set pytest-xdist group
#   * [ ] test with designs: HTB, OSCP, Syslifters, customer designs
# * [ ] designs
#   * [ ] update Calzone/Margherita/Matrix/OSCP/HTB designs: replace @page:first with named pages
# * [ ] documentation
#   * [ ] problem: title page, executive summary, other report data included in PDF
#       * design's HTML templates would need to explicitly support render single findings (e.g. pass a variable to the template for conditional rendering)
#       * solution: post-process the HTML to remove all elements except the finding element (and headers, footers, etc.), then render PDF
#   * [x] data-sysreptor-renderfindings="include|exclude"
#   * [ ] vue variables
#   * [x] might need to update the design's CSS: named pages instead of "@page:first/last"
#   * [x] design: has to set the finding ID as an ID attribute on the finding element (e.g. <div v-for="finding in findings" :id="finding.id">)
#   * [x] limitations
#       * different heading, figure, table, etc. numbers for findings (counters start at 1 for first finding in PDF)
#       * references to other findings or sections do not work (if they are not included in the PDF)

# TODO: discuss:
# * [ ] data-attributes in design AND Vue variables
# * [x] plugin name: "Render Finding PDF" vs. "Export Findings" => "renderfindings"
