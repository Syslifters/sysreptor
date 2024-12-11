import { createApp, compile, computed, defineComponent, type RuntimeCompilerOptions, onBeforeUnmount, onMounted, ref } from 'vue';
import { generateCodeFrame } from '@vue/shared';
import { type CompilerOptions } from '@vue/compiler-core';
import ChartJsPluginDataLabels from 'chartjs-plugin-datalabels';
import lodash from 'lodash';
import Pagebreak from './components/Pagebreak.vue';
import Markdown from './components/Markdown.vue';
import CommaAndJoin from './components/CommaAndJoin.vue';
import TableOfContents from './components/TableOfContents.vue';
import ListOfFigures from './components/ListOfFigures.vue';
import ListOfTables from './components/ListOfTables.vue';
import Chart from './components/ChartVue.vue';
import MermaidDiagram from './components/MermaidDiagram.vue';
import Ref from './components/Ref.vue';
import { callForTicks, getChildElementsRecursive } from './utils';


export type Report = {
  id: string;
  [key: string]: any;
};

export type Finding = {
  id: string;
  created: string;
  order: number;
  [key: string]: any;
};

export type ReportData = {
  report: Report;
  findings: Finding[];
  pentesters: {
    id: string;
    name: string;
    title_before: string;
    first_name: string;
    middle_name: string;
    last_name: string;
    title_after: string;
    email: string;
    phone: string;
    mobile: string;
    roles: string[];
  }[];
};

declare global {
  interface Window {
    RENDERING_COMPLETED: boolean;
    REPORT_TEMPLATE: string;
    REPORT_DATA: ReportData;
  }
}


// injected as global variables
const REPORT_TEMPLATE = '<div>' + (window.REPORT_TEMPLATE || '') + '</div>';
const REPORT_DATA = window.REPORT_DATA || { report: {}, findings: [] };


const templateCompilerOptions: CompilerOptions & RuntimeCompilerOptions = {
  whitespace: 'preserve',
  getTextMode: (node) => {
    // Parse slot content of <markdown> as raw text and do not interpret as html/vue-template
    // TODO: getTextMode gets removed in Vue 3.4 => find an alternative
    return ['markdown', 'mermaid-diagram'].includes(node.tag) ? 2 /* TextModes.RAWTEXT */ : 0 /* TextModes.DATA */;
  },
  isCustomElement: (tag) => ['footnote'].includes(tag),
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
  const app = createApp(defineComponent({
    name: 'root',
    render: RENDER_FUNCTION,
    components: { Pagebreak, Markdown, CommaAndJoin, TableOfContents, ListOfFigures, ListOfTables, Chart, MermaidDiagram, Ref },
    setup() {
      // Data
      const data = REPORT_DATA;
      const findings = computed(() => data.findings);
      const pentesters = computed(() => data.pentesters);
      const report = computed(() => ({ ...data.report, findings: findings.value }));

      // Finding stats
      const findings_info = computed(() => findings.value.filter(f => (f.severity?.value || f.cvss?.level) === 'info'));
      const findings_low = computed(() => findings.value.filter(f => (f.severity?.value || f.cvss?.level) === 'low'));
      const findings_medium = computed(() => findings.value.filter(f => (f.severity?.value || f.cvss?.level) === 'medium'));
      const findings_high = computed(() => findings.value.filter(f => (f.severity?.value || f.cvss?.level) === 'high'));
      const findings_critical = computed(() => findings.value.filter(f => (f.severity?.value || f.cvss?.level) === 'critical'));
      const findings_stats = computed(() => ({
        count_total: findings.value.length,
        count_critical: findings_critical.value.length,
        count_high: findings_high.value.length,
        count_medium: findings_medium.value.length,
        count_low: findings_low.value.length,
        count_info: findings_info.value.length,
      }));

      // Wait until rendering is finished
      const _tickCount = ref<number>(0);
      const _pendingPromises = ref<Promise<void>[]>([]);
      const _observer = new MutationObserver((mutationList) => {
        for (const mutation of mutationList) {
          if (mutation.type === 'childList') {
            for (const an of Array.from(mutation.addedNodes)) {
              for (const node of getChildElementsRecursive(an)) {
                if (node.nodeName === 'SCRIPT') {
                  _pendingPromises.value.push(new Promise((resolve, reject) => {
                    node.addEventListener('load', () => resolve());
                    node.addEventListener('error', reject);
                  }));
                } else if (node.nodeName === 'INPUT' && node.attributes.getNamedItem('type')?.value === 'checkbox' && node.attributes.getNamedItem('checked')) {
                  node.setAttribute('data-checked', 'checked');
                }
              }
            }
          }
        }
      });
      _observer.observe(document, { childList: true, subtree: true });
      onBeforeUnmount(() => _observer.disconnect());
      onMounted(async () => {
        // Wait some ticks before rendering is signaled as completed
        // Allow multi-pass rendering (for e.g. table of contents)
        await callForTicks(10, () => {
          _tickCount.value += 1;
        });
        // Wait for pending promises to finish
        if (_pendingPromises.value.length > 0) {
          await Promise.allSettled(_pendingPromises.value);
          await callForTicks(10, () => {
            _tickCount.value += 1;
          });
        }

        window.RENDERING_COMPLETED = true;
      });

      return {
        data,
        findings,
        pentesters,
        report,
        findings_info,
        findings_low,
        findings_medium,
        findings_high,
        findings_critical,
        findings_stats,
        // Provide libraries and utilities
        chartJsPlugin: {
          DataLabels: ChartJsPluginDataLabels,
        },
        lodash,
        window,
        document,
        computed,
      }
    },
    methods: {
      capitalize(value?: string|null) {
        if (!value) { return ''; }
        value = value.toString()
        return value.charAt(0).toUpperCase() + value.slice(1);
      },
      formatDate(date?: string|null, options: Intl.DateTimeFormatOptions|Intl.DateTimeFormatOptions['dateStyle']|'iso' = 'long', locales: Intl.LocalesArgument = undefined) {
        if (!date) {
          return '';
        }
        const dateObj = new Date(date);
        if (options === 'iso') {
          return new Date(dateObj.getTime() - (dateObj.getTimezoneOffset() * 60000)).toISOString().split("T")[0];
        }
    
        if (typeof options === 'string') {
          options = { dateStyle: options };
        }
        if (!locales) {
          // Get locale from <html lang="...">, since this locale is not automatically applied when formatting dates 
          // (at least in headless chrome, which has poor locale support)
          locales = document.documentElement.lang;
        }
        return dateObj.toLocaleDateString(locales, options);
      },
      cssvar(name: string) {
        const value = window.getComputedStyle(document.documentElement).getPropertyValue(name);
        if (!value) {
          console.warn({
            message: 'CSS variable not defined',
            details: `The CSS variable referenced via cssvar("${name}") does not exist.`,
          });
        }
        return value;
      },
    },
  }));
  app.config.compilerOptions = templateCompilerOptions;
  app.config.warnHandler = (msg, _instance, trace) => {
    if (msg === 'Avoid app logic that relies on enumerating keys on a component instance. The keys will be empty in production mode to avoid performance overhead.') {
      return;
    }
    const warning = {
      message: msg,
      details: trace
    };
    console.warn(warning.message, warning);
  };
  app.config.errorHandler = (err, _instance, info) => {
    const error = {
      message: (err as any).toString() as string,
      details: 'Error in ' + info,
    };
    console.error(error.message, error);
    window.RENDERING_COMPLETED = true;
  };
  app.mount('body');
}

