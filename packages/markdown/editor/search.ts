/* This file is based on @codemirror/search

MIT License

Copyright (C) 2018-2021 by Marijn Haverbeke <marijn@haverbeke.berlin> and others

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
*/


import { closeSearchPanel, findNext, findPrevious, getSearchQuery, replaceAll, replaceNext, SearchQuery, selectMatches, setSearchQuery } from '@codemirror/search';
import { EditorView, ViewPlugin, ViewUpdate, Decoration, type DecorationSet, type Panel, runScopeHandlers } from '@codemirror/view';
import { EditorState, StateEffect, RangeSetBuilder, Prec, StateField } from '@codemirror/state';
import elt from 'crelt';


type QueryType = { spec: SearchQuerySpec; highlight: (state: EditorState, from: number, to: number, add: (from: number, to: number) => void) => void; };
type SearchQuerySpec = SearchQuery & { unquoted?: string; create?: () => QueryType; }

class SearchGlobalState {
  constructor(readonly query: QueryType|null) {}
}
export const setSearchGlobalQuery = StateEffect.define<SearchQuerySpec|null>();
const searchGlobalState: StateField<SearchGlobalState> = StateField.define<SearchGlobalState>({
  create(state) {
    return new SearchGlobalState(null);
  },
  update(value, tr) {
    for (let effect of tr.effects) {
      if (effect.is(setSearchGlobalQuery)) {
        value = new SearchGlobalState(effect.value?.create?.() || null);
      }
    }
    return value;
  },
});


const enum RegExp { HighlightMargin = 250 }
const searchGlobalMatchMark = Decoration.mark({class: "cm-searchGlobalMatch"});
export const searchGlobalHighlighter = ViewPlugin.fromClass(class {
  decorations: DecorationSet

  constructor(readonly view: EditorView) {
    this.decorations = this.highlight(view.state.field(searchGlobalState))
  }

  update(update: ViewUpdate) {
    let state = update.state.field(searchGlobalState)
    if (state != update.startState.field(searchGlobalState) || update.docChanged || update.selectionSet || update.viewportChanged) {
      this.decorations = this.highlight(state)
    }
  }

  highlight({query}: SearchGlobalState) {
    if (!query || !query.spec.unquoted || !query.spec.valid) {
      return Decoration.none;
    }

    let {view} = this
    let builder = new RangeSetBuilder<Decoration>()
    for (let i = 0, ranges = view.visibleRanges, l = ranges.length; i < l; i++) {
      let {from, to} = ranges[i]!;
      while (i < l - 1 && to > ranges[i + 1]!.from - 2 * RegExp.HighlightMargin) {
        to = ranges[++i]!.to
      }
      query.highlight(view.state, from, to, (from, to) => {
        builder.add(from, to, searchGlobalMatchMark);
      });
    }
    return builder.finish()
  }
}, {
  decorations: v => v.decorations
})


export const searchGlobalExtensions = [
  Prec.low(searchGlobalHighlighter),
  searchGlobalState,
];


export class CustomizedSearchPanel implements Panel {
  searchField: HTMLInputElement;
  replaceField: HTMLInputElement;
  dom: HTMLElement;
  query: SearchQuerySpec;

  constructor(readonly view: EditorView) {
    this.query = getSearchQuery(view.state);
    this.commit = this.commit.bind(this);

    function button(name: string, onclick: () => void, icon?: string) {
      return elt("button", {class: "v-btn v-btn--density-compact v-btn--size-small v-btn--variant-default ml-1 ", name, onclick, type: "button"}, [
        elt('span', { class: 'v-btn__overlay' }),
        elt('span', { class: 'v-btn__content' }, [
          name,
          ...(!icon ? [] : [
            elt("i", {class: `v-icon mdi ${icon} mr-1`}),
          ]),
        ]),
      ]);
    }
    this.searchField = elt("input", {
      value: this.query.search,
      placeholder: "Find",
      class: "cm-textfield w-100",
      name: "search",
      form: "",
      spellcheck: "false",
      autocomplete: "off",
      "main-field": "true",
      onchange: this.commit,
      onkeyup: this.commit
    }) as HTMLInputElement;
    this.replaceField = elt("input", {
      value: this.query.replace,
      placeholder: "Replace",
      class: "cm-textfield w-100",
      name: "replace",
      form: "",
      spellcheck: "false",
      autocomplete: "off",
      onchange: this.commit,
      onkeyup: this.commit
    }) as HTMLInputElement;

    this.dom = elt("div", {
      onkeydown: (e: KeyboardEvent) => this.keydown(e), 
      onclick: (e: MouseEvent) => e.stopPropagation(), 
      class: "cm-search d-flex flex-row"
    }, [
      elt('div', [
        this.searchField,
        ...(view.state.readOnly ? [] : [elt('br'), this.replaceField]),
      ]),
      elt('div', [
        button('Next', () => findNext(view), 'mdi-arrow-down'),
        ...(view.state.readOnly ? [] : [elt('br'), button('Replace', () => replaceNext(view))]),
      ]),
      elt('div', [
        button('Previous', () => findPrevious(view), 'mdi-arrow-up'),
        ...(view.state.readOnly ? [] : [elt('br'), button('Replace All', () => replaceAll(view))]),
      ]),
      elt('div', {class: 'flex-grow-1'}),
      elt('div', [
        elt("button", {
          name: "close",
          onclick: () => closeSearchPanel(view),
          type: "button"
        }, [
          elt('i', {class: 'v-icon mdi mdi-close'}),
        ])
      ]),
    ]);
  }

  mount() {
    this.searchField.select()
  }

  update(update: ViewUpdate) {
    for (let tr of update.transactions) {
      for (let effect of tr.effects) {
        if (effect.is(setSearchQuery) && !effect.value.eq(this.query)) {
          this.setQuery(effect.value);
        }
      }
    }
  }

  setQuery(query: SearchQuery) {
    this.query = query
    this.searchField.value = query.search;
    this.replaceField.value = query.replace;
  }

  keydown(e: KeyboardEvent) {
    if (runScopeHandlers(this.view, e, "search-panel")) {
      e.preventDefault()
    } else if (e.code === 'Enter' && e.target == this.searchField) {
      e.preventDefault();
      (e.shiftKey ? findPrevious : findNext)(this.view)
    } else if (e.code === 'Enter' && e.target == this.replaceField) {
      e.preventDefault();
      replaceNext(this.view)
    }
  }

  commit() {
    let query = new SearchQuery({
      search: this.searchField.value,
      replace: this.replaceField.value,
    })
    if (!query.eq(this.query)) {
      this.query = query
      this.view.dispatch({effects: setSearchQuery.of(query)})
    }
  }

  get top() { return true; }
}

