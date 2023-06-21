import { createApp, compile } from 'vue';
import { generateCodeFrame } from '@vue/shared';
import Pagebreak from './components/Pagebreak.vue';  
import Markdown from './components/Markdown.vue';
import CommaAndJoin from './components/CommaAndJoin.js';
import TableOfContents from './components/TableOfContents.js';
import ListOfFigures from './components/ListOfFigures.js';
import ListOfTables from './components/ListOfTables';
import Chart from './components/ChartVue.vue';
import Ref from './components/Ref.vue';
import { callForTicks } from './utils';
import lodash from 'lodash';


// injected as global variables
const REPORT_TEMPLATE = '<div>' + (window.REPORT_TEMPLATE || '') + '</div>';
const REPORT_DATA = window.REPORT_DATA || {report: {}, findings: []};
const REPORT_COMPUTED = window.REPORT_COMPUTED || {};
const REPORT_METHODS = window.REPORT_METHODS || {};


const DEFAULT_COMPUTED = {
  report() {
    return Object.assign({}, this.data.report, {findings: this.findings});
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
    return this.findings.filter(f => f.cvss.level === 'info');
  },
  findings_low() {
    return this.findings.filter(f => f.cvss.level === 'low');
  },
  findings_medium() {
    return this.findings.filter(f => f.cvss.level === 'medium');
  },
  findings_high() {
    return this.findings.filter(f => f.cvss.level === 'high');
  },
  findings_critical() {
    return this.findings.filter(f => f.cvss.level === 'critical');
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
  lodash() {
    return lodash;
  }
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
      options = {dateStyle: options};
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
  isPreTag: () => true,  // Preserve whitespaces of all tags
  getTextMode: (node) => {
    // Parse slot content of <markdown> as raw text and do not interpret as html/vue-template
    return node.tag === 'markdown' ? 2 /* TextModes.RAWTEXT */ : 0 /* TextModes.DATA */;
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
    components: {Pagebreak, Markdown, CommaAndJoin, TableOfContents, ListOfFigures, ListOfTables, Chart, Ref},
    data: () => ({
      data: REPORT_DATA,
      _tickCount: 0,
    }),
    computed: {
      ...DEFAULT_COMPUTED,
      ...REPORT_COMPUTED,
    },
    methods: {
      ...DEFAULT_METHODS,
      ...REPORT_METHODS,
    },
    async mounted() {
      // Wait some ticks before rendering is signaled as completed
      // Allow multi-pass rendering (for e.g. table of contents)
      await callForTicks(5, this.$nextTick, () => { 
        this._tickCount += 1;
      })
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
