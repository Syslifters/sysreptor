import { createApp, compile, computed } from 'vue';
import { generateCodeFrame } from '@vue/shared';
import ChartJsPluginDataLabels from 'chartjs-plugin-datalabels';
import Pagebreak from './components/Pagebreak.vue';
import Markdown from './components/Markdown.vue';
import CommaAndJoin from './components/CommaAndJoin.vue';
import TableOfContents from './components/TableOfContents.vue';
import ListOfFigures from './components/ListOfFigures.vue';
import ListOfTables from './components/ListOfTables.vue';
import Chart from './components/ChartVue.vue';
import MermaidDiagram from './components/MermaidDiagram.vue';
import Ref from './components/Ref.vue';
import { callForTicks, getChildNotesRecursive } from './utils';
import lodash from 'lodash';

// injected as global variables
const REPORT_TEMPLATE = '<div>' + (window.REPORT_TEMPLATE || '') + '</div>';
const REPORT_DATA = window.REPORT_DATA || { report: {}, findings: [] };


const DEFAULT_COMPUTED = {
  report() {
    return Object.assign({}, this.data.report, { findings: this.findings });
  },
  sections() {
    return Object.fromEntries(this.data.sections.map(s => [s.id, s]));
  },
  pentesters() {
    return this.data.pentesters;
  },
  findings() {
    return this.data.findings;
  },
  findings_info() {
    return this.findings.filter(f => (f.severity?.value || f.cvss?.level) === 'info');
  },
  findings_low() {
    return this.findings.filter(f => (f.severity?.value || f.cvss?.level) === 'low');
  },
  findings_medium() {
    return this.findings.filter(f => (f.severity?.value || f.cvss?.level) === 'medium');
  },
  findings_high() {
    return this.findings.filter(f => (f.severity?.value || f.cvss?.level) === 'high');
  },
  findings_critical() {
    return this.findings.filter(f => (f.severity?.value || f.cvss?.level) === 'critical');
  },
  finding_stats() {
    return {
      count_total: this.findings.length,
      count_critical: this.findings_critical.length,
      count_high: this.findings_high.length,
      count_medium: this.findings_medium.length,
      count_low: this.findings_low.length,
      count_info: this.findings_info.length,
    };
  },
  chartjsPlugins() {
    return {
      DataLabels: ChartJsPluginDataLabels
    };
  },
  lodash: () => lodash,
  window: () => window,
  document: () => document,
  computed: () => computed,
};

const DEFAULT_METHODS = {
  capitalize(value) {
    if (!value) { return ''; }
    value = value.toString()
    return value.charAt(0).toUpperCase() + value.slice(1);
  },
  formatDate(date, options = 'long', locales = undefined) {
    if (!date) {
      return '';
    }
    date = new Date(date);
    if (options === 'iso') {
      return new Date(date.getTime() - (date.getTimezoneOffset() * 60000)).toISOString().split("T")[0];
    }

    if (typeof options === 'string') {
      options = { dateStyle: options };
    }
    if (!locales) {
      // Get locale from <html lang="...">, since this locale is not automatically applied when formatting dates 
      // (at least in headless chrome, which has poor locale support)
      locales = document.documentElement.lang;
    }
    return date.toLocaleDateString(locales, options);
  },
  cssvar(name) {
    const value = window.getComputedStyle(document.documentElement).getPropertyValue(name);
    if (!value) {
      console.warn({
        message: 'CSS variable not defined',
        details: `The CSS variable referenced via cssvar("${name}") does not exist.`,
      });
    }
    return value;
  },
}


const templateCompilerOptions = {
  whitespace: 'preserve',
  getTextMode: (node) => {
    // Parse slot content of <markdown> as raw text and do not interpret as html/vue-template
    // TODO: getTextMode gets removed in Vue 3.4 => find an alternative
    return ['markdown', 'mermaid-diagram'].includes(node.tag) ? 2 /* TextModes.RAWTEXT */ : 0 /* TextModes.DATA */;
  },
    isCustomElement: tag => ['footnote'].includes(tag),
  comments: true,
  ssr: false,
  onError: (err) => {
    const error = {
      message: 'Template compilation error: ' + err.message,
      details: err.loc && generateCodeFrame(REPORT_TEMPLATE, err.loc.start.offset, err.loc.end.offset),
    };
    console.error(error.message, error);
    window.RENDERING_COMPLETED = true;
  }
};

const RENDER_FUNCTION = compile(REPORT_TEMPLATE, templateCompilerOptions);


// Skip rendering on template error
if (!window.RENDERING_COMPLETED) {
  const app = createApp({
    name: 'root',
    render: RENDER_FUNCTION,
    components: { Pagebreak, Markdown, CommaAndJoin, TableOfContents, ListOfFigures, ListOfTables, Chart, MermaidDiagram, Ref },
    data: () => ({
      data: REPORT_DATA,
      _tickCount: 0,
      _pendingPromises: [],
      _observer: null,
    }),
    computed: {
      ...DEFAULT_COMPUTED,
    },
    methods: {
      ...DEFAULT_METHODS,
    },
    created() {
      this._observer = new MutationObserver((mutationList) => {
        for (const mutation of mutationList) {
          if (mutation.type === 'childList') {
            for (const an of mutation.addedNodes) {
              for (const node of getChildNotesRecursive(an)) {
                if (node.nodeType === Node.ELEMENT_NODE && node.nodeName === 'SCRIPT') {
                  this._pendingPromises.push(new Promise((resolve, reject) => {
                    node.addEventListener('load', resolve);
                    node.addEventListener('error', reject);
                  }));
                } else if (node.nodeType === Node.ELEMENT_NODE && node.nodeName === 'INPUT' && node.attributes.type.value === 'checkbox' && node.checked) {
                  node.setAttribute('data-checked', 'checked');
                }
              }
            }
          }
        }
      });
      this._observer.observe(document, { childList: true, subtree: true });
    },
    beforeUnmount() {
      this._observer.disconnect();
    },
    async mounted() {
      const waitUntilFinished = async () => {
        // Wait some ticks before rendering is signaled as completed
        // Allow multi-pass rendering (for e.g. table of contents)
        await callForTicks(10, () => {
          this._tickCount += 1;
        });
        // Wait for pending promises to finish
        if (this._pendingPromises.length > 0) {
          await Promise.allSettled(this._pendingPromises);
          await callForTicks(10, () => {
            this._tickCount += 1;
          });
        }
      }
      await waitUntilFinished();

      window.RENDERING_COMPLETED = true;
    },
  });
  app.config.compilerOptions = templateCompilerOptions;
  app.config.warnHandler = (msg, instance, trace) => {
    if (msg === 'Avoid app logic that relies on enumerating keys on a component instance. The keys will be empty in production mode to avoid performance overhead.') {
      return;
    }
    const warning = {
      message: msg,
      details: trace
    };
    console.warn(warning.message, warning);
  };
  app.config.errorHandler = (err, instance, info) => {
    const error = {
      message: err.toString(),
      details: 'Error in ' + info,
    };
    console.error(error.message, error);
    window.RENDERING_COMPLETED = true;
  };
  app.mount('body');

}

