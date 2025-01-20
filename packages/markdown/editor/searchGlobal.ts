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


import { SearchQuery } from '@codemirror/search';
import { EditorView, ViewPlugin, ViewUpdate, Decoration, type DecorationSet } from '@codemirror/view';
import { EditorState, StateEffect, RangeSetBuilder, Prec, StateField } from '@codemirror/state';


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

