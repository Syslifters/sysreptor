# Rendering Workflow
Each pentest project needs a design which specifies how the final report looks like and what fields are available in the report and findings.
The report designer lets you customize how your final PDF reports look like.
We do not limit your report look and feel in any way and allow you to customize your reports to your needs.

PDF rendering is a two-step process.
First, the VueJS template is rendered to plain HTML with Headless Chromium. In this step report variables (section fields, findings) are embedded in the final HTML.
Second, the HTML and CSS styles are rendered to a PDF using WeasyPrint.

![Rendering Workflow](../../images/render-workflow.drawio.png)


## Two rendering engines: Chromium and Weasyprint
You might be wondering why we combine two rendering engines.

The short answer is: To make it easy to design amazing PDF reports with all features expected from a reporting tool. 

And here is the long answer:

The rendering workflow may seem to require lot of resources and slow since we utilize Chromium.

Yes, this approach is resource-intensive and rendering can take some time (typically between 3 and 10 seconds depending on the complexity and size of the report).
However, we want to note that Chromium is not solely responsible for this. 
On average, the VueJS rendering with Chromium takes about 1 second. The remaining time is required by WeasyPrint to generate the PDF.

## WeasyPrint supports advanced CSS printing rules
You may be wondering why we didn't just use Chromium to generate the PDFs and added the slow WeasyPrint.
While Chromium does have a print to PDF feature, it is only suitable for printing web pages to save their content and is not ideal for creating aesthetically pleasing PDFs. 
This is because Chromium has not implemented many CSS rules that are specific to the CSS printing spec, which are crucial for printing and generating PDFs. On the other hand, WeasyPrint was designed specifically to render PDFs and supports many of these printing CSS rules.

## Server-side rendering renders in a single pass
You may also be wondering why we chose to use VueJS with Chromium instead of a simpler or faster template engine to render HTML. 
Most template engines are designed for server-side rendering.
They process the template from start to end, insert variables, evaluate expressions, iterate through loops and output the final HTML.
Everything is rendered in a single pass.


## Complex documents need multi-pass rendering
Let's consider following scenario: 
You are designing a pentest report. It contains a fancy title page, management summary, section with static text (e.g. disclaimer) and list of findings.
You had an interesting pentest and found many vulnerabilities, the report grows in size. 
It is already 50 pages long and its hard to have an overview.
Therefore, you want to add a table of contents to the beginning. 
With single-pass rendering, you would have to generate the table of contents upfront before everything else, because it is on top of the template.

This is not very flexible because the table of contents may contain sections with static texts defined in HTML, finding list, conditional sections that are rendered only in some situations (e.g. list of figures hidden when there are no figures in the report, optional appendix section for portscan results, etc.) or you might event want to include sections/headlines from markdown fields.

## Manual handling of dynamic references is error-prone
When generating the table of contents you would have to make sure that you do not forget anything.
Manually syncing the table of contents with the actual chapters is error-prone, especially, when make quick changes after some time and forget to update the table of contents.

It would be better and more convenient when the table of contents is automatically generated from the renderd HTML content, such that includes all chapters from static text, dynamic finding lists and even markdown text.
The same problem applies for all kind of lists that should be auto-generated based on the content.
Another examples are list of figures or list of tables.
They should include all figures or tables from the whole document.
Figures might occur in static texts from the design or markdown fields of sections or findings.
All should appear in the list of figures, regardless of their source.

## Multi-pass: Render chapters first, then the references 
In order to achive that, we need multi-pass rendering: 
First render the actual chapters, in the second pass collect the defined chapters and render the table of contents.
In LaTeX you need to compile at least twice for all references to be correct (table of contents, bibliography, citings, etc.).

## VueJS is super-dynamic...
Here is where VueJS comes into play. Vue and other client-side JavaScript frameworks (React, Angular, etc.) are designed to be reactive.
When some state changes or users interact with the website (user inputs, clicking, DOM events, etc.), the framework re-renders the HTML.
It natively supports re-rendering parts of the template and therefore we can easily achieve multi-pass rendering.
With Vue we can re-render the table of contents and other references until nothing changes anymore.

## ...and delivers a great ecosystem with additional features
Besides multi-pass rendering, Vue (and JS) are client-side technologies with a great ecosystem of UI libraries, such as [charts](/designer/charts).
We can reuse these libraries for PDF rendering and take advantage of existing, mature, actively maintained and well-documented UI libraries.
