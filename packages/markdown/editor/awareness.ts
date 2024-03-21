import { EditorSelection, RangeSet, RangeValue, SelectionRange, StateEffect, StateField } from "@codemirror/state"
import { EditorView, layer, RectangleMarker } from "@codemirror/view"


export type RemoteClientInfo = {
  name: string;
  color: string;
  selection: EditorSelection;
}
export const setRemoteClients = StateEffect.define<RemoteClientInfo[]>();


class RemoteSelection extends RangeValue {
  constructor(
    readonly clientInfo: RemoteClientInfo,
  ) {
    super();
  }

  static none = RangeSet.empty as RemoteSelectionSet;
}
type RemoteSelectionSet = RangeSet<RemoteSelection>;

const remoteSelectionField = StateField.define<RemoteClientInfo[]>({
  create() {
    return []
  },
  update(value, tr) {
    const remoteClients = tr.effects.find(e => e.is(setRemoteClients))?.value as RemoteClientInfo[]|undefined;
    if (remoteClients) {
      return remoteClients
        // Remove invalid selections
        .filter(c => c.selection.ranges.every(r => r.from >= 0 && r.to <= tr.newDoc.length));
    } else {
      return value.map(c => ({
        ...c,
        selection: c.selection.map(tr.changes)
      }))
    }
  },
});


class ColoredRectangleMarker extends RectangleMarker {
  constructor(
    readonly color: string,
    className: string,
    left: number,
    top: number,
    width: number|null,
    height: number,
  ) {
    super(className, left, top, width, height);
    this.color = color;
  }

  draw(): HTMLDivElement {
    const elt = super.draw();
    elt.style.setProperty('--marker-color', this.color);
    return elt;
  }

  update(elt: HTMLElement, prev: ColoredRectangleMarker): boolean {
      if (prev.color !== this.color) {
        return false;
      }
      const res = super.update(elt, prev);
      if (res) {
        elt.style.backgroundColor = this.color;
      }
      return res;
  }

  eq(p: ColoredRectangleMarker): boolean {
    return super.eq(p) && this.color === p.color;
  }
  
  static forRange2(view: EditorView, className: string, color: string, range: SelectionRange): readonly ColoredRectangleMarker[] {
    return RectangleMarker.forRange(view, className, range)
      .map(m => new ColoredRectangleMarker(color, className, m.left, m.top, m.width, m.height));
  }
}


const remoteSelectionLayer = layer({
  above: false,
  class: 'cm-remoteSelectionLayer',
  markers(view) {
    const out = [] as ColoredRectangleMarker[];
    for (const c of view.state.field(remoteSelectionField)) {
      for (const r of c.selection.ranges) {
        if (!r.empty) {
          out.push(...ColoredRectangleMarker.forRange2(view, 'cm-remoteSelectionBackground', c.color, r));
        }
      }
    }
    return out;
  },
  update(update, layer) {
      return update.docChanged || update.viewportChanged || update.transactions.some(tr => tr.effects.some(e => e.is(setRemoteClients)));
  },
})


const remoteCursorLayer = layer({
  above: true,
  class: 'cm-remoteCursorLayer',
  markers(view) {
    const out = [] as ColoredRectangleMarker[];
    for (const c of view.state.field(remoteSelectionField)) {
      let r = c.selection.main;
      if (!r.empty) {
        r = EditorSelection.cursor(r.head, r.head > r.anchor ? -1 : 1);
      }
      out.push(...ColoredRectangleMarker.forRange2(view, 'cm-remoteCursor', c.color, r));
    }
    return out;
  },
  update(update, layer) {
    return update.docChanged || update.viewportChanged || update.transactions.some(tr => tr.effects.some(e => e.is(setRemoteClients)));
  }
})


const remoteSelectionTheme = EditorView.theme({
  '.cm-remoteSelectionBackground': {
    backgroundColor: 'var(--marker-color)',
    opacity: '0.2',
  },
  '.cm-remoteCursor': {
    borderLeft: '2px solid var(--marker-color)',
    marginLeft: '-1px',
  },
})


export function remoteSelection() {
  return [
    remoteSelectionField, 
    remoteSelectionLayer,
    remoteCursorLayer,
    remoteSelectionTheme,
  ]
}
