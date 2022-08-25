import { createApp, compile } from 'vue';
import { generateCodeFrame } from '@vue/shared';
import Pagebreak from './components/Pagebreak.vue';  
import Markdown from './components/Markdown.vue';
import CommaAndJoin from './components/CommaAndJoin.js';
import TableOfContents from './components/TableOfContents.js';
import ListOfFigures from './components/ListOfFigures.js';
import ListOfTables from './components/ListOfTables';
import Chart from './components/ChartVue.vue';


// injected as global variables
const REPORT_TEMPLAE = window.REPORT_TEMPLATE || '';
const REPORT_DATA = window.REPORT_DATA || {};
const REPORT_COMPUTED = window.REPORT_COMPUTED || {};
const REPORT_METHODS = window.REPORT_METHODS || {};


const DEFAULT_COMPUTED = {
  report() {
    return Object.assign({}, this.data.report, {findings: this.findings});
  },
  findings() {
    return this.data.findings;
  },
  findings_none() {
    return this.findings.filter(f => f.cvss.level === 'none');
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
        count_none: this.findings_none.length,
    };
  }
};

const DEFAULT_METHODS = {
  capitalize(value) {
    if (!value) { return ''; }
    value = value.toString()
    return value.charAt(0).toUpperCase() + value.slice(1);
  },
}


const RENDER_FUNCTION = compile(REPORT_TEMPLAE, {
  whitespace: 'preserve',
  comments: true,
  ssr: false,
  onError: (err) => {
    const error = {
      message: 'Template compilation error: ' + err.message,
      details: err.loc && generateCodeFrame(REPORT_TEMPLAE, err.loc.start.offset, err.loc.end.offset),
    };
    console.error(error.message, error);
    window.RENDERING_COMPLETED = true;
  }
});


// Skip rendering on template error
if (!window.RENDERING_COMPLETED) {
  const app = createApp({
    render: RENDER_FUNCTION,
    components: {Pagebreak, Markdown, CommaAndJoin, TableOfContents, ListOfFigures, ListOfTables, Chart},
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
    mounted() {
      // Wait some ticks before rendering is signaled as completed
      // Allow multi-pass rendering (for e.g. table of contents)
      this.$nextTick(() => {
        this._tickCount += 1;
        this.$nextTick(() => {
          window.RENDERING_COMPLETED = true;
        });
      });
    },
  });
  app.config.errorHandler = (err, instance, info) => {
    const error = {
      message: err.toString(),
      details: 'Error in ' + info,
    };
    console.error(error.message, error);
    window.RENDERING_COMPLETED = true;
  }
  app.mount('body');

}
