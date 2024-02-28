import { v4 as uuid4 } from 'uuid';
import escape from 'lodash/escape';
import unescape from 'lodash/unescape';
import escapeRegExp from 'lodash/escapeRegExp';
import kebabCase from 'lodash/kebabCase';
// @ts-ignore
import { cssLanguage, vueLanguage } from 'reportcreator-markdown/editor';
import { FieldDataType } from "~/utils/types";

export type Node = any;

export type TagInfoAttributes = {
  [key: string]: {
      value: string;
      node: Node;
      nodeName: Node;
      nodeValue: Node;
    }
}

export type TagInfo = {
  node: Node;
  tagName: string;
  tagNameNode: Node;
  attributes: TagInfoAttributes;
  position: DocumentSelectionPosition;
  children: TagInfo[];
}

export type DesignerComponentBlock = {
  tagInfo: TagInfo;
  // eslint-disable-next-line no-use-before-define
  component: DesignerComponent;
  // eslint-disable-next-line no-use-before-define
  context: DesignerContext;
  parent: DesignerComponentBlock|null;
  children: DesignerComponentBlock[];
  childrenArea: DocumentSelectionPosition|null;

  id: string;
  htmlPosition: DocumentSelectionPosition;
  cssPosition: DocumentSelectionPosition|null;
  title: string|null;
  canUpdate: boolean;
};

export type DesignerContext = {
  htmlCode: string;
  cssCode: string;
  projectType: ProjectType;
  htmlTree?: Node[];
  cssTree?: Node;
  componentTree?: DesignerComponentBlock;
};

export type DesignerComponent = {
  type: string;
  name: string;
  allowAsChild: boolean;
  supportsChildren: boolean;

  matches(tagInfo: TagInfo): boolean;
  getTitle(block: DesignerComponentBlock): string|null;

  canCreate: boolean;
  getCreateForm(block: DesignerComponentBlock): any|null;
  createCode(form: any, context: DesignerContext): { html: string; css?: string; }|null;

  getUpdateForm(block: DesignerComponentBlock): any|null;
  update(block: DesignerComponentBlock, form: any): CodeChange[];
};

export class DesignerComponentBlockImpl implements DesignerComponentBlock {
  children: DesignerComponentBlock[];
  childrenArea: DocumentSelectionPosition | null;
  component: DesignerComponent;
  context: DesignerContext;
  cssPosition: DocumentSelectionPosition | null;
  id: string;
  parent: DesignerComponentBlock | null;
  tagInfo: TagInfo;

  constructor({ tagInfo, component, context, parent }: {
    tagInfo: TagInfo,
    component: DesignerComponent,
    context: DesignerContext,
    parent: DesignerComponentBlock|null,
  }) {
    this.tagInfo = tagInfo;
    this.component = component;
    this.context = context;
    this.parent = parent;
    this.children = [];
    this.childrenArea = getChildrenArea(this.tagInfo.node);

    this.id = this.tagInfo.attributes.id?.value || uuid4();
    this.cssPosition = this.findCssPosition();
  }

  get htmlPosition() {
    return this.tagInfo.position;
  }

  findCssPosition() {
    if (!this.tagInfo.attributes.id) { return null; }

    const comments = this.context.cssTree.getChildren('Comment').map((node: Node) => {
      return {
        node,
        text: this.context.cssCode.slice(node.from, node.to).slice(2, -2).trim() as string
      };
    }) as {node: Node; text: string}[];
    const regionStart = comments.find(c => c.text.match(`^#region\\s*${this.id}(\\s|$)`));
    const regionEnd = comments.find(c => c.text.match(`^#endregion\\s*${this.id}(\\s|$)`));
    if (regionStart && regionEnd && regionStart.node.from < regionEnd.node.from) {
      return { from: regionStart.node.from, to: regionEnd.node.to };
    }

    const res = new RegExp(`#${escapeRegExp(this.tagInfo.attributes.id.value)}(\\s|\\.|{)`).exec(this.context.cssCode);
    if (res) {
      return { from: res.index, to: res.index };
    }
    return null;
  }

  get title(): string|null {
    return this.component.getTitle(this);
  }

  get canUpdate(): boolean {
    return !!this.component.getUpdateForm(this);
  }
}

export class DesignerComponentBase implements DesignerComponent {
  allowAsChild: boolean;
  name: string;
  supportsChildren: boolean;
  type: string;

  constructor({ type, name, allowAsChild, supportsChildren }: {
    type: string;
    name: string
    allowAsChild?: boolean;
    supportsChildren?: boolean;
  }) {
    this.type = type;
    this.name = name;
    this.allowAsChild = allowAsChild || false;
    this.supportsChildren = supportsChildren || false;
  }

  matches(tagInfo: TagInfo): boolean {
    return tagInfo.attributes['data-sysreptor-generated']?.value === this.type || tagInfo.tagName === this.type;
  }

  getTitle(_block: DesignerComponentBlock): string|null {
    return null;
  }

  getCreateForm(): any|null {
    return null;
  }

  createCode(_form: any, _context: DesignerContext): { html: string; css?: string }|null {
    return null;
  }

  get canCreate(): boolean {
    return !!this.getCreateForm();
  }

  getUpdateForm(_block: DesignerComponentBlock): any|null {
    return null;
  }

  update(_block: DesignerComponentBlock, _form: any): CodeChange[] {
    return [];
  }
}

export class TextSectionComponent extends DesignerComponentBase {
  constructor() {
    super({ type: 'content', name: 'Content', allowAsChild: true, supportsChildren: true });
  }

  matches(tagInfo: TagInfo) {
    return ['div', 'section'].includes(tagInfo.tagName) &&
      tagInfo.children.some(c => ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].includes(c.tagName) ||
                                 new FindingListComponent().matches(c));
  }

  getCreateForm() {
    return {
      form: 'section-create',
      headline: new HeadlineComponent().getCreateForm().headline,
      markdown: Object.assign(new MarkdownComponent().getCreateForm().markdown, { text: 'TODO: Text **with** _markdown_ `code`' }),
    };
  }

  createCode(form: any, context: DesignerContext) {
    return {
      html: `
        <div>
          ${new HeadlineComponent().createCode(form, context).html}
          ${new MarkdownComponent().createCode(form, context)!.html}
        </div>
      `,
    };
  }
}

export class HeadlineComponent extends DesignerComponentBase {
  constructor() {
    super({ type: 'headline', name: 'Headline', allowAsChild: true });
  }

  matches(tagInfo: TagInfo) {
    return ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].includes(tagInfo.tagName);
  }

  getTitle(block: DesignerComponentBlock) {
    return getTagContent(block.context.htmlCode, { childrenArea: block.childrenArea })
  }

  get canCreate() {
    return false;
  }

  getUpdateForm(block: DesignerComponentBlock) {
    const classes = (block.tagInfo.attributes.class?.value || '').split(' ');
    return {
      form: 'headline',
      headline: {
        text: unescape(getTagContent(block.context.htmlCode, { childrenArea: block.childrenArea })),
        tag: block.tagInfo.tagName.toLowerCase(),
        intoc: classes.includes('in-toc'),
        numbered: classes.includes('numbered'),
      },
    };
  }

  htmlFromForm(form: any, attrs?: {[key: string]: string}) {
    attrs = attrs || {};
    const classes = new Set((attrs?.class || '').split(' '));
    if (form.headline.intoc) { classes.add('in-toc'); } else { classes.delete('in-toc'); }
    if (form.headline.numbered) { classes.add('numbered'); } else { classes.delete('numbered'); }
    if (classes.size > 0) {
      attrs.class = Array.from(classes).join(' ').trim();
    } else {
      delete attrs.class;
    }
    const attrsStr = Object.entries(attrs).map(([attrName, attrValue]) => `${attrName}="${attrValue}"`).join(' ');
    return `<${form.headline.tag} ${attrsStr}>${escape(form.headline.text)}</${form.headline.tag}>`;
  }

  update(block: DesignerComponentBlock, form: any) {
    const attrs = Object.fromEntries(Object.entries(block.tagInfo.attributes).map(([n, v]) => [n, v.value]));
    return [{
      type: 'html',
      from: block.tagInfo.node.from,
      deleteCount: block.tagInfo.node.to - block.tagInfo.node.from,
      add: this.htmlFromForm(form, attrs),
    }];
  }

  getCreateForm() {
    return {
      form: 'headline',
      headline: {
        tag: 'h1',
        text: 'Headline Title',
        intoc: true,
        numbered: true,
      }
    };
  }

  createCode(form: any, context: DesignerContext) {
    return { html: this.htmlFromForm(form, { id: createUniqueId(kebabCase(form.headline.text || 'heading'), context) }) };
  }
}

export class MarkdownComponent extends DesignerComponentBase {
  constructor() {
    super({ type: 'markdown', name: 'Markdown', allowAsChild: true });
  }

  matches(tagInfo: TagInfo) {
    return tagInfo.tagName === 'markdown';
  }

  getTitle(block: DesignerComponentBlock) {
    if (block.tagInfo.attributes[':text']) {
      return block.tagInfo.attributes[':text'].value;
    }
    const mdFirstLine = trimLeadingWhitespace(getTagContent(block.context.htmlCode, { childrenArea: block.childrenArea })).split('\n')[0];
    const headline = mdFirstLine.match(/^#+\s+(?<headline>.*)/)?.groups?.headline;
    if (headline) {
      return headline;
    }
    return null;
  }

  getUpdateForm(block: DesignerComponentBlock) {
    if (block.childrenArea && !block.tagInfo.attributes[':text']) {
      return {
        form: 'markdown-text',
        markdown: {
          text: trimLeadingWhitespace(getTagContent(block.context.htmlCode, { childrenArea: block.childrenArea }))
        }
      };
    } else {
      return {
        form: 'markdown-variable',
        markdown: {
          variable: block.tagInfo.attributes[':text']?.value,
        }
      };
    }
  }

  update(block: DesignerComponentBlock, form: any) {
    if (form.form === 'markdown-text') {
      let text = form.markdown.text;
      text = '\n' + text + '\n';
      return [
        { type: 'html', from: block.childrenArea!.from, deleteCount: block.childrenArea!.to - block.childrenArea!.from, add: text }
      ];
    } else if (form.form === 'markdown-variable') {
      if (block.tagInfo.attributes[':text']) {
        const attrValueNode = block.tagInfo.attributes[':text'].nodeValue;
        return [{ type: 'html', from: attrValueNode.from, deleteCount: attrValueNode.to - attrValueNode.from, add: form.markdown.variable || '' }];
      } else {
        return [{ type: 'html', from: block.tagInfo.tagNameNode.from, deleteCount: 0, add: ` :text="${form.markdown.variable || ''}"` }];
      }
    }
    return [];
  }

  getCreateForm() {
    return {
      form: 'markdown-create',
      markdown: {
        form: 'text',
        text: '# Headline {.in-toc.numbered}\nTODO: Text **with** _markdown_ `code`',
        variable: '',
      }
    };
  }

  createCode(form: any, _context: DesignerContext) {
    if (form.markdown.form === 'text') {
      return { html: `<markdown>\n${form.markdown.text}\n</markdown>` };
    } else if (form.markdown.form === 'variable') {
      return { html: `<markdown :text="${form.markdown.variable || ''}"></markdown>` };
    } else {
      return null;
    }
  }
}

export class ParagraphComponent extends DesignerComponentBase {
  constructor() {
    super({ type: 'paragraph', name: 'Paragraph', allowAsChild: true });
  }

  matches(tagInfo: TagInfo) {
    return tagInfo.tagName === 'p';
  }
}

export class AppendixComponent extends DesignerComponentBase {
  constructor() {
    super({ type: 'appendix', name: 'Appendix', supportsChildren: true });
  }

  matches(tagInfo: TagInfo) {
    return ['div', 'section'].includes(tagInfo.tagName) && (tagInfo.attributes.class?.value || '').split(' ').includes('appendix');
  }

  getCreateForm() {
    const form = new HeadlineComponent().getCreateForm();
    form.headline.text = 'Appendix';
    return form;
  }

  createCode(form: any, context: DesignerContext) {
    let dynamicAppendixSection = `
    <div v-for="appendix_section in report.appendix_sections">
      <h2 class="in-toc numbered">{{ appendix_section.title }}</h2>
      <markdown :text="appendix_section.text" />
    </div>
    `;
    const appendixField = context?.projectType?.report_fields?.appendix_sections;
    if (!appendixField || appendixField?.type !== 'list' || appendixField?.items?.type !== 'object' ||
    appendixField?.items?.properties?.title?.type !== 'string' ||
    appendixField?.items?.properties?.content?.type !== 'markdown') {
      dynamicAppendixSection = '<!--\n' + dynamicAppendixSection + '\n-->';
    }
    return {
      html: trimLeadingWhitespace(`
        <section class="appendix">
          ${new HeadlineComponent().createCode(form, context).html}

          <markdown>
            ## Static Appendix Section {.in-toc.numbered}
            TODO: Appendix section content
          </markdown>

          ${dynamicAppendixSection}
        </section>
      `),
    }
  }
}

export class ChartComponent extends DesignerComponentBase {
  constructor() {
    super({ type: 'chart', name: 'Findings Chart' });
  }

  matches(tagInfo: TagInfo) {
    return tagInfo.tagName === 'chart' || (tagInfo.tagName === 'figure' && tagInfo.children.some(c => c.tagName === 'chart'));
  }

  getTitle(block: DesignerComponentBlock) {
    const caption = block.tagInfo.children.find(c => c.tagName === 'figcaption');
    if (!caption) { return null; }
    return getTagContent(block.context.htmlCode, { node: caption.node });
  }

  getCreateForm() {
    return {
      form: 'chart-create',
      chart: {
        chartType: 'bar (horizontal)', // pie, doughnut
        caption: 'Distribution of identified vulnerabilities',
      }
    };
  }

  createCode(form: any, context: DesignerContext) {
    const id = createUniqueId(kebabCase(form.chart.caption || 'chart'), context);
    if (form.chart.chartType == "bar (vertical)") {
      return {
        html: trimLeadingWhitespace(`
        <figure>
          <chart :width="15" :height="10" :config="{
                plugins: [ chartjsPlugins.DataLabels ],
                type: 'bar', 
                data: {
                labels: ['Critical', 'High', 'Medium', 'Low', 'Info'],
                datasets: [
                    {
                        data: [
                            finding_stats.count_critical,
                            finding_stats.count_high,
                            finding_stats.count_medium,
                            finding_stats.count_low,
                            finding_stats.count_info
                        ],
                        backgroundColor: [
                            cssvar('--color-risk-critical'), 
                            cssvar('--color-risk-high'), 
                            cssvar('--color-risk-medium'), 
                            cssvar('--color-risk-low'), 
                            cssvar('--color-risk-info')
                        ],
                        datalabels: {
                            align: 'start',
                            anchor: 'end',
                            display: function(context) {
                                return context.dataset.data[context.dataIndex] !== 0; // Hide datalabel if value is 0
                            }
                        }
                    }
                ]
                },
                options: {
                    layout: {
                        padding: {
                            left: 25,
                            right: 25,
                            top: 25,
                            bottom: 25
                        }
                    },
                    indexAxis: 'y',
                    scales: {
                        y: {
                            grid: {display: false},
                            beginAtZero: true,
                            ticks: {
                                padding: 5,
                                z: 1,
                                color: ['#505050'],
                                font: {
                                    size: 25,
                                    family: 'Noto Sans'
                                }
                            }
                        },
                        x: {
                            grid: {
                                display: true,
                                color: 'grey'
                            },
                            ticks: {
                                display: true,
                                precision: 0,
                                color: '#505050',
                                font: {
                                    size: 25,
                                    family: 'Noto Sans'
                                }
                            }
                        }
                    }, 
                    plugins: {
                        legend: {display: false},
                        datalabels: {
                            display: 'auto',
                            padding: {
                                right: 15,
                            },
                            color: ['white'],
                            font: {
                                size: 25
                            },
                        }
                    },
                }
            }" />
          <figcaption id="${id}">${form.chart.caption}</figcaption>
        </figure>`)
      };
    } else if (form.chart.chartType == "pie") {
      return {
        html: trimLeadingWhitespace(`
        <figure>
          <chart :width="15" :height="10" :config="{
                plugins: [ chartjsPlugins.DataLabels ],
                type: 'pie', 
                data: {
                    labels: ['Critical', 'High', 'Medium', 'Low', 'Info'],
                    datasets: [
                        {
                            data: [
                                finding_stats.count_critical,
                                finding_stats.count_high,
                                finding_stats.count_medium,
                                finding_stats.count_low,
                                finding_stats.count_info
                            ],
                            backgroundColor: [
                                cssvar('--color-risk-critical'), 
                                cssvar('--color-risk-high'), 
                                cssvar('--color-risk-medium'), 
                                cssvar('--color-risk-low'), 
                                cssvar('--color-risk-info')
                            ],
                            datalabels: {
                                anchor: 'end',
                                align: 'start',
                                formatter: function(value, context) {
                                    return value + ' ' + context.chart.data.labels[context.dataIndex]; // Add label to datalabel
                                }
                            }
                        }
                    ]
                },
                options: {
                    layout: {
                        padding: {
                            left: 25,
                            right: 25,
                            top: 25,
                            bottom: 25
                        }
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'right',
                            labels: {
                                color: '#505050',
                                font: {
                                    size: 25
                                }
                            }
                        },
                        datalabels: {
                            display: 'auto',
                            padding: {
                                top: 25,
                                bottom: 25,
                                right: 25,
                                left: 25,
                            },
                            color: ['white'],
                            font: {
                                size: 25
                            },
                        }
                    },
                }
            }" />
          <figcaption id="${id}">${form.chart.caption}</figcaption>
        </figure>`)
      };
    } else if (form.chart.chartType == "doughnut") {
      return {
        html: trimLeadingWhitespace(`
        <figure>
          <chart :width="15" :height="10" :config="{
                plugins: [ chartjsPlugins.DataLabels ],
                type: 'doughnut', 
                data: {
                    labels: ['Critical', 'High', 'Medium', 'Low', 'Info'],
                    datasets: [
                        {
                            data: [
                                finding_stats.count_critical,
                                finding_stats.count_high,
                                finding_stats.count_medium,
                                finding_stats.count_low,
                                finding_stats.count_info
                            ],
                            backgroundColor: [
                                cssvar('--color-risk-critical'), 
                                cssvar('--color-risk-high'), 
                                cssvar('--color-risk-medium'), 
                                cssvar('--color-risk-low'), 
                                cssvar('--color-risk-info')
                            ],
                            datalabels: {
                                anchor: 'end',
                                align: 'start',
                            }
                        }
                    ]
                },
                options: {
                    layout: {
                        padding: {
                            left: 25,
                            right: 25,
                            top: 25,
                            bottom: 25
                        }
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'right',
                            labels: {
                                color: '#505050',
                                font: {
                                    size: 25
                                }
                            }
                        },
                        datalabels: {
                            display: 'auto',
                            padding: {
                                top: 25,
                                bottom: 25,
                                right: 25,
                                left: 25,
                            },
                            color: ['white'],
                            font: {
                                size: 25
                            },
                            display: function(context) {
                                return context.dataset.data[context.dataIndex] !== 0; // Hide datalabel if value is 0
                            },
                        }
                    },
                }
            }" />
          <figcaption id="${id}">${form.chart.caption}</figcaption>
        </figure>`)
      };
    } else if (form.chart.chartType == "polarArea") {
      return {
        html: trimLeadingWhitespace(`
        <figure>
          <chart :width="15" :height="10" :config="{
                plugins: [ chartjsPlugins.DataLabels ],
                type: 'polarArea', 
                data: {
                    labels: ['Critical', 'High', 'Medium', 'Low', 'Info'],
                    datasets: [
                        {
                            data: [
                                finding_stats.count_critical,
                                finding_stats.count_high,
                                finding_stats.count_medium,
                                finding_stats.count_low,
                                finding_stats.count_info
                            ],
                            backgroundColor: [  
                                cssvar('--color-risk-critical'), 
                                cssvar('--color-risk-high'), 
                                cssvar('--color-risk-medium'), 
                                cssvar('--color-risk-low'), 
                                cssvar('--color-risk-info')
                            ],
                            datalabels: {
                                anchor: 'center',
                                align: 'center'
                            }
                        }
                    ]
                },
                options: {
                    scales: {
                        r: {
                            ticks: {
                                precision: 0,
                                display: false,
                                z: 1,
                                font: {
                                    size: 25,
                                    family: 'Noto Sans'
                                }
                            },
                            grid: {color: 'grey'}
                        }
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'right',
                            labels: {
                                color: '#505050',
                                font: {
                                    size: 25
                                }
                            }
                        },
                        datalabels: {
                            display: 'auto',
                            padding: {
                                top: 25,
                                bottom: 25,
                                right: 25,
                                left: 25,
                            },
                            color: ['white'],
                            font: {
                                size: 25
                            },
                        }
                    },
                }
            }" />
          <figcaption id="${id}">${form.chart.caption}</figcaption>
        </figure>`)
      };
    } else if (form.chart.chartType == "radar") {
      return {
        html: trimLeadingWhitespace(`
        <figure>
          <chart :width="15" :height="10" :config="{
            type: 'radar', 
            data: {
                labels: ['Critical', 'High', 'Medium', 'Low', 'Info'],
                datasets: [
                    {
                        data: [
                            finding_stats.count_critical,
                            finding_stats.count_high,
                            finding_stats.count_medium,
                            finding_stats.count_low,
                            finding_stats.count_info
                        ],
                        backgroundColor: [
                            'rgba(232, 50, 33, 0.5)'
                        ],
                    }
                ]
            },
            options: {
                scales: {
                    r: {
                        grid: {color: 'grey'},
                        pointLabels: {
                            font: {
                               size: 25,
                               family: 'Noto Sans'
                           }
                        },
                        ticks: {
                            precision: 0,
                            display: true,
                            font: {
                                  size: 25,
                                  family: 'Noto Sans'
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false,
                        position: 'right',
                        labels: {
                            font: {
                                size: 25
                            }
                        }
                    }
                },
            }
        }" />
          <figcaption id="${id}">${form.chart.caption}</figcaption>
        </figure>`)
      };
    } else {
      // horizontal bar or line
      return {
        html: trimLeadingWhitespace(`
        <figure>
          <chart :width="15" :height="10" :config="{
              plugins: [ chartjsPlugins.DataLabels ],
              type: '${(form.chart.chartType == "line") ? "line" : "bar"}', 
              data: {
                  labels: ['Critical', 'High', 'Medium', 'Low', 'Info'],
                  datasets: [
                      {
                          data: [
                              finding_stats.count_critical,
                              finding_stats.count_high,
                              finding_stats.count_medium,
                              finding_stats.count_low,
                              finding_stats.count_info
                          ],
                          backgroundColor: [
                              cssvar('--color-risk-critical'), 
                              cssvar('--color-risk-high'), 
                              cssvar('--color-risk-medium'), 
                              cssvar('--color-risk-low'), 
                              cssvar('--color-risk-info')
                          ],
                          datalabels: {
                              display: function(context) {
                                  return context.dataset.data[context.dataIndex] !== 0; // Hide datalabel if value is 0
                              }
                          }
                      }
                  ]
              },
              options: {
                  layout: {
                  padding: {
                      left: 50,
                      right: 50,
                      top: 50,
                      bottom: 50
                  }
              },
              scales: {
                  y: {
                      grid:{
                          display: true,
                          color: 'grey'
                      },
                      beginAtZero: true,
                      ticks: {
                          precision: 0,
                          color: '#505050',
                          font: {
                              size: 25,
                              family: 'Noto Sans',
                          }
                      }
                  },
                  x: {
                      grid: {
                          display: false
                      },
                      ticks: {
                          color: '#505050',
                          font: {
                              size: 25,
                              family: 'Noto Sans',
                          }
                      }
                  }
              },
              plugins: {
                  legend: {
                      display: false,
                      labels: {
                          font: {
                              size: 25
                          }
                      }
                  },
                  datalabels: {
                      display: 'auto',
                      padding: {
                          right: 15,
                          },
                          color: ['white'],
                          font: {
                              size: 25
                          },
                      }
                  },
              }
          }" />
          <figcaption id="${id}">${form.chart.caption}</figcaption>
        </figure>`)
      };
    }
  }
}

export class FindingListComponent extends DesignerComponentBase {
  constructor() {
    super({ type: 'finding-list', name: 'Finding List', supportsChildren: true });
  }

  matches(tagInfo: TagInfo) {
    return ['div', 'section', 'template'].includes(tagInfo.tagName) &&
      [' in findings', 'in report.findings'].some(m => (tagInfo.attributes['v-for']?.value || '').includes(m));
  }
}

export class FindingsChapterComponent extends DesignerComponentBase {
  constructor() {
    super({ type: 'findings-chapter', name: 'Findings', supportsChildren: true });
  }

  matches(tagInfo: TagInfo) {
    return new TextSectionComponent().matches(tagInfo) && tagInfo.children.some(new FindingListComponent().matches);
  }

  getCreateForm() {
    return {
      form: 'finding-list-create',
      findingList: {
        headline: 'Findings',
        headerVariant: 'default', // table
      },
    };
  }

  createCode(form: any, context: DesignerContext) {
    const id = createUniqueId('findings', context);
    let htmlHeader = '';
    let htmlFields = '';
    let css = '';
    if (form.findingList.headerVariant === 'default') {
      htmlHeader = trimLeadingWhitespace(`
        <h2 :id="finding.id" class="in-toc numbered">{{ finding.title }}</h2>
        <div class="finding-header">
          <strong>Criticality: </strong><span :class="'risk-' + finding.cvss.level">{{ lodash.capitalize(finding.cvss.level) }}</span><br />
          <strong>CVSS-Score: </strong><span :class="'risk-' + finding.cvss.level">{{ finding.cvss.score }}</span><br />
          <strong>CVSS-Vector: </strong>{{ finding.cvss.vector }}<br />
      `);
      if ('affected_components' in context.projectType.finding_fields) {
        htmlHeader += '\n' + trimLeadingWhitespace(`
          <template v-if="finding.affected_components && finding.affected_components.length > 0">
            <strong>Affects: </strong>
            <markdown v-if="finding.affected_components.length == 1" :text="finding.affected_components[0]" class="markdown-inline" />
            <ul v-else class="location-ul">
              <li v-for="component in finding.affected_components">
                <markdown :text="component" class="markdown-inline" />
              </li>
            </ul>
          </template>
        `);
      }
      htmlHeader += '</div>';
    } else if (form.findingList.headerVariant === 'table') {
      htmlHeader = trimLeadingWhitespace(`
        <table class="finding-header">
          <thead>
            <tr>
              <th colspan="2" class="finding-header-key text-center"><h2 :id="finding.id" class="in-toc">{{ finding.title }}</h2></th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="finding-header-key">CVSS-Score</td>
              <td :class="'risk-bg-' + finding.cvss.level">{{ finding.cvss.score }} ({{ lodash.capitalize(finding.cvss.level) }}</td>
            </tr>
            <tr>
              <td class="finding-header-key">CVSS-Vector</td>
              <td>{{ finding.cvss.vector }}</td>
            </tr>
      `);
      css += trimLeadingWhitespace(`
        #${id} .finding-header-key {
          font-weight: bold;
          background-color: #ABABAB;
        }
      `);

      if ('affected_components' in context.projectType.finding_fields) {
        htmlHeader += '\n' + trimLeadingWhitespace(`
          <tr v-if="finding.affected_components && finding.affected_components.length > 0">
            <td class="finding-header-key">Affects</td>
            <td>
              <markdown v-if="finding.affected_components.length == 1" :text="finding.affected_components[0]" class="markdown-inline" />
              <ul v-else class="location-ul">
                <li v-for="component in finding.affected_components">
                  <markdown :text="component" class="markdown-inline" />
                </li>
              </ul>
            </td>
          </tr>
        `);
      }
      htmlHeader += '\n  </tbody>\n</table>';
    }

    const includeFields = context.projectType.finding_field_order
      .filter(f => !['title', 'cvss', 'affected_components', 'short_recommendation'].includes(f))
      .map(f => [f, context.projectType.finding_fields[f]])
      .filter(([_f, d]) => (d as FieldDefinition).type === FieldDataType.MARKDOWN);
    for (const [f, d] of includeFields) {
      htmlFields += trimLeadingWhitespace(`
        <div v-if="finding.${f}">
          <h3 :id="finding.id + '-${f}'">${(d as FieldDefinition).label}</h3>
          <markdown :text="finding.${f}" />
        </div>
      `);
    }
    return {
      html: trimLeadingWhitespace(`
        <section id="${id}">
          <h1 id="${id}-headline" class="in-toc numbered">${form.findingList.headline}</h1>
          <div v-for="finding in findings">
            ${htmlHeader}
            ${htmlFields}
            <pagebreak />
          </div>
        </section>
      `),
      css: css ? `/* #region ${id} */\n` + css + `\n/* #endregion ${id} */` : undefined,
    }
  }
}

export class PagebreakComponent extends DesignerComponentBase {
  constructor() {
    super({ type: 'pagebreak', name: 'Page Break' });
  }

  matches(tagInfo: TagInfo) {
    return tagInfo.tagName === 'pagebreak';
  }

  get canCreate() {
    return true;
  }

  createCode() {
    return { html: '<pagebreak />' };
  }
}

export class TableOfContentsComponent extends DesignerComponentBase {
  constructor() {
    super({ type: 'table-of-contents', name: 'Table of Contents' });
  }

  matches(tagInfo: TagInfo) {
    return tagInfo.tagName === 'table-of-contents';
  }

  getCreateForm() {
    return {
      form: 'toc-create',
      toc: {
        headline: 'Table of Contents',
        variant: 'default', // compact
        leader: true,
      }
    };
  }

  createCode(form: any, context: DesignerContext) {
    const id = createUniqueId('toc', context);
    const cssCommon = trimLeadingWhitespace(`
      #${id} li {
        list-style: none;
        margin: 0;
        padding: 0;
      }
      #${id} .ref::before {
          padding-right: 0.5em;
      }
      #${id} .ref::after {
          content: " " leader("${form.toc.leader ? '.' : ' '}") " " target-counter(attr(href), page);
      }
    `);
    const cssDefault = trimLeadingWhitespace(`
      #${id} .toc-level1 {
        font-size: 1.5rem;
        font-weight: bold;
        margin-top: 0.8rem;
      }
      #${id} .toc-level2 {
        font-size: 1.2rem;
        font-weight: bold;
        margin-top: 0.5rem;
        margin-left: 2rem;
      }
      #${id} .toc-level3 {
        font-size: 1rem;
        margin-top: 0.4rem;
        margin-left: 4rem;
      }
      #${id} .toc-level4 {
        font-size: 1rem;
        margin-top: 0;
        margin-left: 6rem;
      }
    `);
    const cssCompact = trimLeadingWhitespace(`
      #${id} .toc-level1 {
        padding-left: 0;
        margin-top: 0.7rem;
        font-weight: bold;
      }
      #${id} .toc-level2 {
        padding-left: 1.5rem;
        margin-top: 0.35rem;
        font-weight: normal;
      }
      #${id} .toc-level3 {
        padding-left: 3rem;
        margin-top: 0.25rem;
        font-weight: normal;
      }
      #${id} .toc-level4 {
        padding-left: 4.5rem;
        margin-top: 0;
        font-weight: normal;
      }
    `);

    return {
      html: trimLeadingWhitespace(`
        <table-of-contents id="${id}" v-slot="tocItems" >
          <h1>${form.toc.headline}</h1>
          <ul>
              <li v-for="item in tocItems" :class="'toc-level' + item.level">
                  <ref :to="item.id" />
              </li>
          </ul>
          <pagebreak />
        </table-of-contents>
      `),
      css: `/* #region ${id} */\n` +
           cssCommon + '\n' +
           ({ default: cssDefault, compact: cssCompact }[form.toc.variant as string] || '') + '\n' +
           `/* #endregion ${id} */`
    };
  }
}

export class ListOfFiguresComponent extends DesignerComponentBase {
  constructor() {
    super({ type: 'list-of-figures', name: 'List of Figures' });
  }

  matches(tagInfo: TagInfo) {
    return tagInfo.tagName === 'list-of-figures';
  }

  get canCreate() {
    return true;
  }

  createCode(_form: any, context: DesignerContext) {
    const id = createUniqueId('lof', context);
    return {
      html: trimLeadingWhitespace(`
        <list-of-figures id="${id}" v-slot="items" >
          <section v-if="items.length > 0">
              <h1 class="in-toc">List of Figures</h1>
              <ul>
                  <li v-for="item in items">
                      <ref :to="item.id" />
                  </li>
              </ul>
              <pagebreak />
          </section>
        </list-of-figures>`),
      css: trimLeadingWhitespace(`
        /* #region ${id} */
        #${id} li {
          list-style: none;
          margin: 0;
          padding: 0;
        }
        #${id} .ref-figure::before {
            content: var(--prefix-figure) target-counter(attr(href), figure-counter) " - ";
        }
        #${id} .ref-figure > .ref-title {
            display: inline;
        }
        #${id} .ref-figure::after {
            content: " " leader(".") " " target-counter(attr(href), page);
        }
        /* #endregion ${id} */
        `),
    };
  }
}

export class PageHeaderComponent extends DesignerComponentBase {
  constructor() {
    super({ type: 'page-header', name: 'Page Header' });
  }

  matches(tagInfo: TagInfo) {
    return tagInfo.attributes['data-sysreptor-generated']?.value === 'page-header';
  }

  getCreateForm() {
    return {
      form: 'header-create',
      header: {
        backgroundColor: null,
        left: null,
        right: 'logo',
      }
    }
  }

  createCode(form: any, context: DesignerContext) {
    function getHeaderTypeContent(headerType: string) {
      if (headerType === 'logo') {
        return `<img src="/assets/name/logo.png" alt="logo" />`;
      } else if (headerType === 'text') {
        return '<strong>TODO Company Name</strong><br>\nExample Street 47 | 4771 Example<br>\nFN 12345 v | District Court Example<br>';
      }
      return '';
    }

    function backgroundColorSnippet(text: string) {
      if (!form.header.backgroundColor) {
        return '';
      }
      return text;
    }

    const id = createUniqueId('header', context);
    let html = `<div id="${id}" data-sysreptor-generated="page-header">\n`;
    let css = trimLeadingWhitespace(`
    @page {
        margin-top: 35mm;

        --header-margin-bottom: 5mm;
        ${backgroundColorSnippet('--header-background-color: ' + form.header.backgroundColor + ';')}

        @top-left-corner {
            content: "";
            margin-bottom: var(--header-margin-bottom);
            ${backgroundColorSnippet('background-color: var(--header-background-color);')}
        }
        @top-left {
            content: ${form.header.left ? 'element(' + id + '-left)' : '""'};
            margin-bottom: var(--header-margin-bottom);
            ${backgroundColorSnippet('background-color: var(--header-background-color);')}
            ${backgroundColorSnippet('width: 51%;')}
            ${backgroundColorSnippet('margin-left: -1px;')}
            ${backgroundColorSnippet('margin-right: -1px;')}
        }
        @top-right {
            content: ${form.header.right ? 'element(' + id + '-right)' : '""'};
            margin-bottom: var(--header-margin-bottom);
            ${backgroundColorSnippet('background-color: var(--header-background-color);')}
            ${backgroundColorSnippet('width: 51%;')}
            ${backgroundColorSnippet('margin-left: -1px;')}
            ${backgroundColorSnippet('margin-right: -1px;')}
        }
        @top-right-corner {
            content: "";
            margin-bottom: var(--header-margin-bottom);
            ${backgroundColorSnippet('background-color: var(--header-background-color);')}
        }
    }

    #${id} { position: absolute; width: 0; }
    `) + '\n';
    if (form.header.left) {
      html += `<div id="${id}-left">\n${getHeaderTypeContent(form.header.left)}\n</div>\n`;
      css += `#${id}-left { position: running(${id}-left); }\n`;
      if (form.header.left === 'logo') {
        css += `#${id}-left { height: 100%; width: auto; }\n#${id}-left img { width: auto; height: auto; }\n`;
      }
    }
    if (form.header.right) {
      html += `<div id="${id}-right">\n${getHeaderTypeContent(form.header.right)}\n</div>\n`;
      css += `#${id}-right { position: running(${id}-right); text-align: right; }\n`;
      if (form.header.right === 'logo') {
        css += `#${id}-right { height: 100%; width: auto; }\n#${id}-right img { width: auto; height: auto; }\n`;
      }
    }
    html += '</div>\n';
    return {
      html,
      css: `/* #region ${id} */\n${css}/* #endregion ${id} */`,
    };
  }
}

export class PageFooterComponent extends DesignerComponentBase {
  constructor() {
    super({ type: 'page-footer', name: 'Page Footer' });
  }

  matches(tagInfo: TagInfo) {
    return tagInfo.attributes['data-sysreptor-generated']?.value === 'page-footer';
  }

  getCreateForm() {
    return {
      form: 'footer-create',
      footer: {
        textLeft: '',
        textCenter: '',
        pageNumberStyle: 'page', // page-of, none
      }
    };
  }

  createCode(form: any, context: DesignerContext) {
    const id = createUniqueId('footer', context);
    let html = `<div id="${id}" data-sysreptor-generated="page-footer">\n`;
    let css = `#${id} { position: absolute; width: 0; }\n`;
    let cssPage = '';
    if (form.footer.textLeft) {
      html += `<div id="${id}-left">${form.footer.textLeft}</div>\n`;
      css += `#${id}-left { position: running(footer-left); }\n`;
      cssPage += `    @bottom-left { content: element(footer-left); }\n`;
    }
    if (form.footer.textCenter) {
      html += `<div id="${id}-center">${form.footer.textCenter}</div>\n`;
      css += `#${id}-center { position: running(footer-center); }\n`;
      cssPage += `    @bottom-center { content: element(footer-center); }\n`;
    }
    if (['page', 'page-of'].includes(form.footer.pageNumberStyle)) {
      const counterContents: {[key: string]: string} = {
        page: 'counter(page)',
        'page-of': 'counter(page) " / " counter(pages)',
      };
      cssPage += `    @bottom-right-corner { content: ${counterContents[form.footer.pageNumberStyle]}; }\n`;
    }
    html += '</div>';
    if (cssPage) {
      css = `@page {\n${cssPage}}\n` + css;
    }
    css = `/* #region ${id} */\n${css}/* #endregion ${id} */`;
    return { html, css };
  }
}

export class CoverPageComponent extends DesignerComponentBase {
  constructor() {
    super({ type: 'cover-page', name: 'Cover Page' });
  }

  matches(tagInfo: TagInfo) {
    return tagInfo.attributes['data-sysreptor-generated']?.value === 'page-cover';
  }

  getCreateForm() {
    return {
      form: 'page-cover-create',
      coverPage: {
        background: null,
        hideHeader: true,
        hideFooter: true,
      }
    };
  }

  createCode(form: any, context: DesignerContext) {
    const id = createUniqueId('page-cover', context);
    const html = trimLeadingWhitespace(`
      <section id="${id}" data-sysreptor-generated="page-cover">
        <div class="page-cover-title">
          <h1>PENTEST REPORT</h1>
          <h2>{{ report.title }}</h2>
        </div>
        <div class="page-cover-customer">
          <p>
            <strong>Customer:</strong><br>
            ${'customer' in context.projectType.report_fields ? '{{ report.customer }}' : 'Example Customer'}<br>
            ${'document_history' in context.projectType.report_fields ? 
              "{{ report.document_history[report.document_history.length - 1]?.date || '' }}<br>" +
              "{{ report.document_history[report.document_history.length - 1]?.version || '0.0' }}<br>" : ""
            }
          </p>
        </div>
        <pagebreak />
      </section>
    `);

    let pageCss = '';
    if (form.coverPage.background === 'color') {
      pageCss += `  background-color: #ff0000;\n\n`;
    }
    if (form.coverPage.background === 'image') {
      pageCss += `  background-image: url("/assets/name/background.png");\n`;
      pageCss += `  background-repeat: no-repeat;\n`;
      pageCss += `  background-size: cover;\n`;
      pageCss += `  background-position: center;\n`
      pageCss += `  background-attachment: fixed;\n\n`;
    }
    if (form.coverPage.hideHeader) {
      pageCss += '  /* Hide header */\n';
      pageCss += '  @top-left-corner { content: none !important; }\n';
      pageCss += '  @top-left { content: none !important; }\n';
      pageCss += '  @top-center { content: none !important; }\n';
      pageCss += '  @top-right { content: none !important; }\n';
      pageCss += '  @top-right-corner { content: none !important; }\n';
    }
    if (form.coverPage.hideFooter) {
      pageCss += '  /* Hide footer */\n';
      pageCss += '  @bottom-left-corner { content: none !important; }\n';
      pageCss += '  @bottom-left { content: none !important; }\n';
      pageCss += '  @bottom-center { content: none !important; }\n';
      pageCss += '  @bottom-right { content: none !important; }\n';
      pageCss += '  @bottom-right-corner { content: none !important; }\n';
    }

    let css = trimLeadingWhitespace(`
      #${id} {
        page: ${id};
      }
    `) + '\n';
    if (pageCss) {
      css += `@page ${id} {\n${pageCss}}\n`;
    }

    css += trimLeadingWhitespace(`
      #${id} .page-cover-title {
        position: absolute;
        top: 20mm;
        left: 0;
        width: 14cm;
      }
      #${id} .page-cover-customer {
        position: absolute;
        top: 11cm;
        left: 0;
        width: 14cm;
      }
    `) + '\n';

    return {
      html,
      css: `/* #region ${id} */\n${css}/* #endregion ${id} */`,
    };
  }
}

export const unknownComponent = new DesignerComponentBase({ type: 'unknown', name: 'Code' });
export const rootWrapperComponent = new DesignerComponentBase({ type: 'root', name: 'Root', supportsChildren: true });

export const designerComponents: DesignerComponent[] = [
  new PageHeaderComponent(),
  new PageFooterComponent(),
  new CoverPageComponent(),
  new TableOfContentsComponent(),
  new ListOfFiguresComponent(),

  new MarkdownComponent(),
  new HeadlineComponent(),
  new PagebreakComponent(),
  new ParagraphComponent(),
  new ChartComponent(),

  // Containers
  new FindingsChapterComponent(),
  new FindingListComponent(),
  new AppendixComponent(),
  new TextSectionComponent(),
];

export const predefinedDesignerComponentGroups = [
  {
    name: 'Page Styles',
    components: [
      new PageHeaderComponent(),
      new PageFooterComponent(),
      new CoverPageComponent(),
    ],
  },
  {
    name: 'Chapters',
    components: [
      new TableOfContentsComponent(),
      new ListOfFiguresComponent(),
      new FindingsChapterComponent(),
      new AppendixComponent(),
      new TextSectionComponent(),
    ]
  },
  {
    name: 'Elements',
    components: [
      new PagebreakComponent(),
      new MarkdownComponent(),
      new ChartComponent(),
    ]
  }
];

export const initialCss = trimLeadingWhitespace(`
  @import "/assets/global/base.css";

  /* Define variables */
  :root {
      --color-risk-critical: #FF2600;
      --color-risk-high: #FF9300;
      --color-risk-medium: #FFDA00;
      --color-risk-low: #0096FF;
      --color-risk-info: #00AE51;
  }

  /* Font settings */
  html {
      font-family: "Noto Sans", sans-serif;
      font-size: 10pt;
  }

  /* Classes for risk colors */
  .risk-critical { color: var(--color-risk-critical) !important; font-weight: bold; }
  .risk-high { color: var(--color-risk-high) !important; font-weight: bold; }
  .risk-medium { color: var(--color-risk-medium) !important; font-weight: bold; }
  .risk-low { color: var(--color-risk-low) !important; font-weight: bold; }
  .risk-info { color: var(--color-risk-info) !important; font-weight: bold; }

  .risk-bg-critical { background-color: var(--color-risk-critical) !important; }
  .risk-bg-high { background-color: var(--color-risk-high) !important; }
  .risk-bg-medium { background-color: var(--color-risk-medium) !important; }
  .risk-bg-low { background-color: var(--color-risk-low) !important; }
  .risk-bg-info { background-color: var(--color-risk-info) !important; }
`);

function getTagInfo(text: string, node: Node): TagInfo|null {
  if (node.type.name !== 'Element') {
    return null;
  }
  const openTag = node.firstChild;
  if (!['SelfClosingTag', 'OpenTag'].includes(openTag.type.name)) {
    return null;
  }
  const tagName = openTag.getChild('TagName');
  if (!tagName) {
    return null;
  }

  return {
    node,
    tagName: text.slice(tagName.from, tagName.to).toLowerCase(),
    tagNameNode: tagName,
    attributes: Object.fromEntries(openTag.getChildren('Attribute').map((a: Node) => {
      const nodeName = a.getChild('AttributeName') || a.getChild('VueAttributeName');
      let name = null;
      if (nodeName) {
        name = text.slice(nodeName.from, nodeName.to).toLowerCase();
      } else if (a.firstChild.type.name === ':' && a.firstChild.nextSibling.type.name === 'Identifier') {
        name = ':' + text.slice(a.firstChild.nextSibling.from, a.firstChild.nextSibling.to);
      }
      if (!name) {
        return null;
      }
      const nodeValue = a.getChild('AttributeValue') || a.getChild('ScriptAttributeValue');
      let value = nodeValue ? text.slice(nodeValue.from, nodeValue.to) : true;
      if ((typeof value === 'string') && ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'")))) {
        value = value.slice(1, -1);
      }
      return [name, { value, node: a, nodeName, nodeValue }];
    }).filter((a: any|null) => !!a)),
    position: {
      from: node.from,
      to: node.to,
    },
    children: getChildTagInfos(text, node),
  };
}

function getChildTagInfos(text: string, node: Node): TagInfo[] {
  return node.getChildren('Element').map((c: Node) => getTagInfo(text, c)).filter((t: TagInfo|null) => !!t);
}

function getChildrenArea(node: Node): DocumentSelectionPosition|null {
  if (!node || node.type.name !== 'Element' || node.firstChild.type.name !== 'OpenTag' || node.lastChild.type.name !== 'CloseTag') {
    return null;
  }
  return {
    from: node.firstChild.nextSibling.from,
    to: node.lastChild.prevSibling.to
  };
}

function getTagContent(text: string, { childrenArea, node }: { childrenArea?: DocumentSelectionPosition|null, node?: Node }): string {
  if (!childrenArea) {
    childrenArea = getChildrenArea(node);
  }
  if (!childrenArea) {
    return '';
  }
  return text.slice(childrenArea.from, childrenArea.to);
}

function trimLeadingWhitespace(str: string): string {
  /*
    Get the initial indentation
    But ignore new line characters
  */
  const matcher = /^[\r\n]?(\s+)/;
  if (matcher.test(str)) {
    /*
      Replace the initial whitespace
      globally and over multiple lines
    */
    return str.replace(new RegExp("^" + str.match(matcher)![1], "gm"), "").trim();
  } else {
    // Regex doesn't match so return the original string
    return str;
  }
}

function createUniqueId(baseId: string, context: DesignerContext) {
  let id = baseId;
  for (let i = 1; context.htmlCode.includes(`id="${id}"`); i++) {
    id = `${baseId}-${i}`;
  }
  return id;
}

/**
* Return a tree of HTML components with their location in the HTML and CSS structure.
* Component types are defined by the attribute data-sysreptor-generated="<component-name>" and have an ID.
* CSS rules for components are prefixed with the component ID.
*/
export function parseToComponentTree(htmlCode: string, cssCode: string, projectType: ProjectType): DesignerComponentBlock {
  const context = {
    htmlCode,
    cssCode,
    projectType
  } as DesignerContext;
  const topNode = vueLanguage.parser.parse(htmlCode).topNode;
  const htmlTree = getChildTagInfos(htmlCode, topNode);
  context.htmlTree = htmlTree;
  context.cssTree = cssLanguage.parser.parse(context.cssCode).topNode;

  let root = null;
  if (htmlTree.length === 1 && htmlTree[0].tagName === 'div' && Object.entries(htmlTree[0].attributes).length === 0) {
    root = new DesignerComponentBlockImpl({
      tagInfo: htmlTree[0],
      component: rootWrapperComponent,
      parent: null,
      context,
    });
  } else {
    root = new DesignerComponentBlockImpl({
      tagInfo: {
        node: topNode,
        tagName: 'template',
        tagNameNode: topNode,
        attributes: {},
        children: htmlTree,
        position: {
          from: 0,
          to: context.htmlCode.length,
        }
      },
      component: rootWrapperComponent,
      parent: null,
      context,
    });
    root.childrenArea = root.tagInfo.position;
  }
  root.children = formatTree(root.tagInfo.children, { parent: root });
  context.componentTree = root;
  return root;

  function formatTree(tagInfoList: TagInfo[], { parent }: { parent?: DesignerComponentBlock } = {}) {
    return tagInfoList.map((tagInfo) => {
      const component = designerComponents.find(c => c.matches(tagInfo)) || unknownComponent;
      const out = new DesignerComponentBlockImpl({
        tagInfo,
        component,
        parent: parent || null,
        context,
      });
      if (out.component.supportsChildren) {
        out.children = formatTree(tagInfo.children, { parent: out });
      }
      return out;
    });
  }
}

export default {};
