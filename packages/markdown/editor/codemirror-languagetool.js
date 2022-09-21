import { renderMarkdown } from "../index.js";
import {debounce} from 'lodash';
import './codemirror-languagetool.css';

const MAX_REPLACEMENTS = 5;
const DEBOUNCE_TIME = 500;


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


function SpellcheckState(cm, CodeMirror) {
  this.cm = cm;
  this.CodeMirror = CodeMirror;
  
  this.onMouseOver = function (e) {
    onMouseOver(cm, e);
  };
  this.timeout = null;
  this.waitingFor = 0;
  this.errors = [];
}

// Tooltip
function onMouseOver(cm, e) {
  let target = e.target || e.srcElement;
  if (target.className.indexOf("CodeMirror-spellcheck-mark") < 0) return;

  let box = target.getBoundingClientRect(), x = (box.left + box.right) / 2, y = (box.top + box.bottom) / 2;
  let spans = cm.findMarksAt(cm.coordsChar({left: x, top: y}, "client"));
  if (!spans.length || spans.length === 0) return;

  let span;
  for (let i = 0; i < spans.length; ++i) {
    if (spans[i].__annotation) {
      if (span) console.warn("more than one possible span for spellcheck tooltips, things may get dicey", spans);
      span = spans[i];
    }
  }

  // only show if it is not already being displayed
  if (!span.__annotation.__tooltip) {
    span.__annotation.__tooltip = true; // reduce race conditions by pre-setting tooltip "cache" as soon as possible
    showTooltipFor(cm, e, span, target);
  }
}

function showTooltipFor(cm, e, span, target) {
  let CodeMirror = cm.state.spellcheck.CodeMirror;

  let [tooltip, closeButton] = makeTooltip(cm, CodeMirror, e, span);
  span.__annotation.__tooltip = tooltip;

  // remove immediately removes the tooltip, which we only really want for the close button and garbage collection
  // everything else should use hide
  function remove() {
    span.__annotation.__tooltip = null;
    if (tooltip && tooltip.parentNode) tooltip.parentNode.removeChild(tooltip);
  }

  closeButton.addEventListener("click", remove);

  // to allow the user to move to the tooltip even after leaving the target element we have a timeout (hider)
  // that is triggered on leaving the marked text
  // if the user reaches the tooltip within this timeout the hiding is canceled, the same is true for the other
  // way around
  let hider;

  function hide() {
    // check if the tooltip even exists anymore
    if (!tooltip || !tooltip.parentNode) return;

    // start the fade out transition and fully remove it after another timeout
    tooltip.style.opacity = "0";

    // the hider can be canceled by the clearHide function
    hider = setTimeout(remove, 350); // timeout for fadeout
  }

  target.addEventListener("mouseleave", hide);
  tooltip.addEventListener("mouseleave", hide);

  function clearHide() {
    if (!hider) return;
    clearTimeout(hider);
    tooltip.style.opacity = "1";
    hider = null;
  }

  target.addEventListener("mouseover", clearHide);
  tooltip.addEventListener("mouseover", clearHide);

  // finally to clear up all left-over tooltips that occur due to various codemirror operations we have
  // garbage collection run ever so often (directly taken from CodeMirrors lint.js with lowered frequency)
  let garbageCollect = setInterval(function () {
    if (!tooltip) return clearInterval(garbageCollect);
    for (let n = target; ; n = n.parentNode) {
      if (n && n.nodeType === 11) n = n.host;
      if (n === document.body) return;
      if (!n) {
        remove()
        break;
      }
    }
  }, 8000);
}

function makeTooltip(cm, CodeMirror, e, span) {
  let tooltip = document.createElement("div");
  tooltip.className = "CodeMirror-spellcheck-tooltip cm-s-" + cm.options.theme;

  let messages = document.createElement("div");
  const ann = span.__annotation;
  let tip = document.createElement("div");
  tip.className = "CodeMirror-spellcheck-message";

  let title = document.createElement("div");
  title.className = "CodeMirror-spellcheck-tooltip-title CodeMirror-spellcheck-tooltip-title-" + ann.errorType;
  let bold = document.createElement("b");
  bold.appendChild(document.createTextNode(ann.rule.category.name))
  title.appendChild(bold);
  tip.appendChild(title);

  let message = document.createElement("div");
  message.className = "CodeMirror-spellcheck-tooltip-message";
  message.appendChild(document.createTextNode(ann.message));
  if (ann.rule.urls && ann.rule.urls.length > 0) {
    let moreDetails = document.createElement("a");
    moreDetails.className = "CodeMirror-spellcheck-tooltip-more-details";
    moreDetails.href = ann.rule.urls[0].value;
    moreDetails.target = "_blank";
    moreDetails.rel = "noreferrer noopener";
    message.appendChild(moreDetails);
  }
  tip.appendChild(message);

  let replacements = document.createElement("ul");
  for (let j = 0; j < ann.replacements.length && j < MAX_REPLACEMENTS; j++) {
    let entry = document.createElement("li");
    let replacement = document.createElement("a");
    let suggestion = ann.replacements[j].value;
    if (suggestion === " ") {
      suggestion = "␣";
    } else {
      if (suggestion.startsWith(" ")) {
        suggestion = "\u00A0" + suggestion.substring(1);
      }
      if (suggestion.endsWith(" ")) {
        suggestion = suggestion.substring(0, suggestion.length - 1) + "\u00A0";
      }
    }
    replacement.appendChild(document.createTextNode(suggestion));
    replacement.href = "#";
    replacement.addEventListener("click", function (e) {
      e.preventDefault();
      const location = span.find();
      cm.replaceRange(ann.replacements[j].value, location.from, location.to);
      span.__annotation.__tooltip = null;
      if (tooltip && tooltip.parentNode) tooltip.parentNode.removeChild(tooltip);
    })
    entry.appendChild(replacement);
    replacements.appendChild(entry);
  }
  tip.appendChild(replacements);
  let closeButton = document.createElement("span");
  closeButton.className = "CodeMirror-spellcheck-tooltip-close";
  tip.appendChild(closeButton);
  messages.appendChild(tip);

  tooltip.appendChild(messages);
  cm.getWrapperElement().appendChild(tooltip);

  const rect = e.target.getBoundingClientRect();
  tooltip.style.top = Math.max(0, rect.bottom) + "px";
  tooltip.style.left = Math.max(rect.left, Math.min(rect.right - 12, e.clientX)) + "px";
  if (tooltip.style.opacity != null) tooltip.style.opacity = 1;

  return [tooltip, closeButton];
}

function clearErrors(cm) {
  let state = cm.state.spellcheck;
  if (!state) {
    return;
  }

  for (let i = 0; i < state.errors.length; ++i) {
    state.errors[i].clear();
  }
  state.errors.length = 0;
}

function updateErrors(cm, text, errors) {
  clearErrors(cm);

  let state = cm.state.spellcheck;
  if (!state) {
    return;
  }

  const Pos = state.CodeMirror.Pos;
  for (let i = 0; i < errors.length; i++) {
    const error = errors[i];

    let errorType = "grammar";
    if (SPELLING_RULE_IDS.some(e => error.rule.id.includes(e))) {
      errorType = "spelling";
    } else if (STYLE_ISSUE_TYPES.some(e => error.rule.issueType === e)) {
      errorType = "style";
    }
    error["errorType"] = errorType;

    const marker = cm.markText(cm.posFromIndex(error.offset), cm.posFromIndex(error.offset+error.length), {
      className: "CodeMirror-spellcheck-mark CodeMirror-spellcheck-mark-" + errorType,
      __annotation: error,
    });
    state.errors.push(marker);
  }
}

function spellcheck(cm) {
  if (!cm.state.spellcheck || !cm.options.spellcheckLanguage) {
    return;
  }

  let state = cm.state.spellcheck;
  let id = ++state.waitingFor;

  function abort() {
    id = -1;
    cm.off("change", abort);
  }
  cm.on("change", abort);

  const text = cm.getValue();
  const annotatedText = renderMarkdown(text, {to: 'annotatedText'});
  cm.off("change", abort)
  if (annotatedText.length === 0) {
    // nothing to check
    clearErrors(cm);
    return;
  }
  // check if we have been aborted by the extractor lazy loader
  if (id === -1) {
    return;
  }

  cm.options.performSpellcheckRequest({
    language: cm.options.spellcheckLanguage,
    data: {annotation: annotatedText},
  })
    .then(results => {
      if (state.waitingFor !== id) {
        return;
      }

      // TODO: check the rest of the returned data, especially warnings for errors in processing
      cm.operation(() => updateErrors(cm, text, results.matches));
    })
    .catch(err => console.error('Spellcheck error', err));
}

const onChange = debounce(spellcheck, DEBOUNCE_TIME);


export default function codeMirrorLanguageTool({codeMirrorInstance: cmi}) {
  cmi.defineOption("spellcheck", null, (cm, val, old) => {
    // Enable/disable spellcheck
    if (val && !cm.state.spellcheck) {
      let state = cm.state.spellcheck = new SpellcheckState(cm, cmi);
      cm.on("change", onChange);
      cmi.on(cm.getWrapperElement(), "mouseover", state.onMouseOver);
      spellcheck(cm);
    } else if (!val && cm.state.spellcheck) {
      let state = cm.state.spellcheck;
      cm.off("change", onChange);
      cmi.off(cm.getWrapperElement(), "mouseover", state.onMouseOver);
      clearErrors(cm);
      cm.state.spellcheck = null;
    }
  });
  cmi.defineOption('spellcheckLanguage', null, (cm, val, old) => {
    if (val !== old && cm.state.spellcheck) {
      spellcheck(cm);
    }
  });
  cmi.defineOption('performSpellcheckRequest', null);

  cmi.defineExtension("performSpellcheck", function () {
    if (this.state.spellcheck) { 
      spellcheck(this);
    }
  });
}
