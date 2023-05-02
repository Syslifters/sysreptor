import { markdownToAnnotatedText } from "..";
import { linter, setDiagnostics, forEachDiagnostic } from "@codemirror/lint";
import elt from "crelt";
import { EditorView } from "@codemirror/view";


const MAX_REPLACEMENTS = 5;
const SPELLING_RULE_IDS = [
  "SPELLER_RULE",
  "MORFOLOGIK_RULE",
  "HUNSPELL",
  "SPELLING_RULE"
];
const STYLE_ISSUE_TYPES = [
  "style",
  "locale-violation",
  "register"
];


export function spellcheck({ performSpellcheckRequest, performSpellcheckAddWordRequest }) {
  return linter(async (view) => {
    const annotatedText = markdownToAnnotatedText(view.state.doc.toString());
    if (annotatedText.length === 0) {
      return [];
    }

    const spellcheckResults = await performSpellcheckRequest({
      data: {annotation: annotatedText},
    });
    
    return spellcheckResults.matches.map(m => {
      const severity = SPELLING_RULE_IDS.some(r => m.rule.id.includes(r)) ? 'error' :
                       STYLE_ISSUE_TYPES.some(r => m.rule.id.includes(r)) ? 'info' : 
                       'warning';
      const from = m.offset;
      const to = Math.min(m.offset + m.length, view.state.doc.length);
      return {
        from,
        to,
        severity: severity,
        renderMessage() {
          return elt('div', {class: 'cm-spellcheck-content'},
            elt('div', {class: 'cm-spellcheck-title cm-spellcheck-title-' + severity}, m.rule.category.name),
            elt('div', {class: 'cm-spellcheck-message'}, 
              m.message,
              m.rule.urls?.length > 0 ? elt('a', {href: m.rule.urls[0].value, target: '_blank', rel: 'noreferrer noopener', class: 'cm-spellcheck-details'}) : null,
            ),
          );
        },
        actions: m.replacements.slice(0, MAX_REPLACEMENTS).map(r => ({
          name: r.value,
          apply(view, from, to) {
            view.dispatch({changes: {from, to, insert: r.value}});
          }
        })).concat((performSpellcheckAddWordRequest && severity === 'error') ? [{
          name: `Add "${view.state.doc.sliceString(from, to)}" to dictionary`,
          async apply(view, from, to) {
            const word = view.state.doc.sliceString(from, to);
            await performSpellcheckAddWordRequest({ word });
            
            // remove spellcheck errors for word
            const diagnostics = []
            forEachDiagnostic(view.state, (d, from, to) => {
              if (!(d.severity === 'error' && view.state.doc.sliceString(from, to) == word)) {
                diagnostics.push(d);
              }
            });
            view.dispatch(setDiagnostics(view.state, diagnostics));
          }
        }] : []),
      };
    });
  }, {delay: 750});
}


function svg(content, attrs = `viewBox="0 0 40 40"`) {
  return `url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" ${attrs}>${encodeURIComponent(content)}</svg>')`
}

function underline(color) {
  return svg(`<path d="m0 2.5 l2 -1.5 l1 0 l2 1.5 l1 0" stroke="${color}" fill="none" stroke-width=".7"/>`,
             `width="6" height="3"`)
}

export const spellcheckTheme = EditorView.theme({
  '.cm-diagnostic': {
    listStyle: 'none',
    fontSize: '10pt',
    maxWidth: '400px',
    backgroundColor: 'white',
    paddingBottom: '0.5em',
  },
  '.cm-diagnosticText': {
    display: 'block',
    marginBottom: '0.5em',
  },
  '.cm-diagnosticAction': {
    backgroundColor: '#45a8fc',
    color: 'white',
    marginLeft: '0',
    marginRight: '8px',
    '&:hover': {
      backgroundColor: '#1976d2'
    },
  },
  [`.cm-diagnosticAction[aria-label*="Add "][aria-label*=" to dictionary"]`]: {
    display: 'block',
    backgroundColor: 'inherit',
    color: 'gray',
    width: '100%',
    textAlign: 'center',
    marginTop: '0.5em',
    '&:hover': {
      backgroundColor: 'rgba(0, 0, 0, 0.05)',
    },
  },
  '.cm-spellcheck-details': {
    opacity: '0.7',
    background: 'transparent url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEwIDRhNiA2IDAgMTAwIDEyIDYgNiAwIDAwMC0xMnptMC0xYTcgNyAwIDExMCAxNCA3IDcgMCAwMTAtMTR6bS0uNSA2aDFhLjUuNSAwIDExMCAxdjNhLjUuNSAwIDExMCAxaC0xYS41LjUgMCAxMTAtMXYtM2EuNS41IDAgMDEwLTF6bS41LTFhMSAxIDAgMTEwLTIgMSAxIDAgMDEwIDJ6IiBmaWxsPSIjM0MzRjQ5IiBmaWxsLXJ1bGU9ImV2ZW5vZGQiLz48L3N2Zz4=) 50% no-repeat',
    backgroundSize: '100% 100%',
    display: 'inline-block',
    marginBottom: '-0.3em',
    marginLeft: '0.2em',
  },
  '.cm-spellcheck-title': {
    fontWeight: 'bold',
    paddingLeft: '1.3em',
  },
  '.cm-spellcheck-title:before': {
    content: '""',
    height: '0.6em',
    width: '0.6em',
    borderRadius: '50%',
    position: 'absolute',
    left: '1em',
    top: '0.5em',
  },
  '.cm-spellcheck-title-error:before': { background: '#f91a47' },
  '.cm-spellcheck-title-warning:before': { background: 'orange' },
  '.cm-spellcheck-title-info:before': { background: '#5c4cff' },

  ".cm-diagnostic-error": { borderLeft: "5px solid #f91a47" },
  ".cm-diagnostic-warning": { borderLeft: "5px solid orange" },
  ".cm-diagnostic-info": { borderLeft: "5px solid #5c4cff" },

  '.cm-lintRange-error': { backgroundImage: underline('#f91a47') },
  '.cm-lintRange-warning': { backgroundImage: underline('orange') },
  '.cm-lintRange-info': { backgroundImage: underline('#5c4cff') },
});
