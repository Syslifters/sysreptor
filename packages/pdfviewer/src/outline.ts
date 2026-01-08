import { PDFDocumentProxy, stopEvent } from "pdfjs-dist";
import { EventBus, PDFLinkService } from "pdfjs-dist/web/pdf_viewer.mjs";

type PDFOutline = Awaited<ReturnType<PDFDocumentProxy['getOutline']>>;
type PDFOutlineItem = PDFOutline[number];

export type PDFOutlineViewerOptions = {
  container: HTMLElement;
  eventBus: EventBus;
  linkService: PDFLinkService;
}


export class PDFOutlineViewer {
  options: PDFOutlineViewerOptions;
  pdfDocument: PDFDocumentProxy|null = null;
  outline: PDFOutline|null = null;

  constructor(options: PDFOutlineViewerOptions) {
    this.options = options;
  }

  async setDocument(pdfDocument: PDFDocumentProxy) {
    this.reset();
    this.pdfDocument = pdfDocument;
    this.outline = await this.pdfDocument.getOutline();
    this.render();
  }

  reset() {
    this.pdfDocument = null;
    this.outline = null;

    // Remove the tree from the DOM.
    this.options.container.replaceChildren();
    // Ensure that the left (right in RTL locales) margin is always reset,
    // to prevent incorrect tree alignment if a new document is opened.
    this.options.container.classList.remove("withNesting");
  }

  render() {
    const fragment = document.createDocumentFragment() as DocumentFragment|HTMLElement;
    const queue = [{ parent: fragment, items: this.outline }];
    let outlineCount = 0;
    let hasAnyNesting = false;
    while (queue.length > 0) {
      const levelData = queue.shift()!;
      for (const item of levelData.items || []) {
        const div = document.createElement("div");
        div.className = "treeItem";

        const element = document.createElement("a");
        this._bindLink(element, item);
        this._setStyles(element, item);
        element.textContent = this._normalizeTextContent(item.title);

        div.append(element);

        if (item.items.length > 0) {
          hasAnyNesting = true;
          this._addToggleButton(div, item);

          const itemsDiv = document.createElement("div");
          itemsDiv.className = "treeItems";
          div.append(itemsDiv);

          queue.push({ parent: itemsDiv, items: item.items });
        }

        levelData.parent.append(div);
        outlineCount++;
      }
    }

    if (hasAnyNesting) {
      this.options.container.classList.add("withNesting");
      this.options.container.addEventListener('click', e => {
        const target = e.target as HTMLElement|null;
        if (!target?.classList.contains("treeItemToggler")) {
          return;
        }
        stopEvent(e);
        target.classList.toggle("treeItemsHidden");
        if (e.shiftKey) {
          const shouldShowAll = !target.classList.contains("treeItemsHidden");
          this._toggleTreeItem(this.options.container, shouldShowAll);
        }
      });
    }
    this.options.container.append(fragment);
  }

  _bindLink(element: HTMLAnchorElement, item: Partial<PDFOutlineItem>) {
    const linkService = this.options.linkService;

    if (item.url) {
      linkService.addLinkAttributes(element, item.url, item.newWindow);
      return;
    }

    if (item.dest) {
      element.href = linkService.getDestinationHash(item.dest);
      element.addEventListener('click', () => linkService.goToDestination(item.dest!));
    }
  }

  _setStyles(element: HTMLElement, item: Partial<PDFOutlineItem>) {
    if (item.bold) {
      element.style.fontWeight = "bold";
    }
    if (item.italic) {
      element.style.fontStyle = "italic";
    }
  }

  _normalizeTextContent(str: string): string {
    // Chars in range [0x01-0x1F] will be replaced with a white space
    // and 0x00 by "".
    return (
      removeNullCharacters(str, /* replaceInvisible */ true) ||
      /* en dash = */ "\u2013"
    );
  }

  _addToggleButton(div: HTMLElement, item: PDFOutlineItem) {
    let hidden = false;
    const count = item.count || 0;
    if (count < 0) {
      let totalCount = item.items.length;
      if (totalCount > 0) {
        const queue = [...item.items];
        while (queue.length > 0) {
          const { count: nestedCount, items: nestedItems } = queue.shift();
          if (nestedCount > 0 && nestedItems.length > 0) {
            totalCount += nestedItems.length;
            queue.push(...nestedItems);
          }
        }
      }
      if (Math.abs(count) === totalCount) {
        hidden = true;
      }
    }

    const toggler = document.createElement("div");
    toggler.className = "treeItemToggler";
    if (hidden) {
      toggler.classList.add("treeItemsHidden");
    }
    div.prepend(toggler);
  }

  /**
   * Collapse or expand the subtree of a tree item.
   */
  _toggleTreeItem(root: HTMLElement, show = false) {
    for (const toggler of root.querySelectorAll(".treeItemToggler")) {
      toggler.classList.toggle("treeItemsHidden", !show);
    }
  }
}


function removeNullCharacters(str: string, replaceInvisible = false) {
  const InvisibleCharsRegExp = /[\x00-\x1F]/g;
  if (!InvisibleCharsRegExp.test(str)) {
    return str;
  }
  if (replaceInvisible) {
    return str.replaceAll(InvisibleCharsRegExp, m => (m === "\x00" ? "" : " "));
  }
  return str.replaceAll("\x00", "");
}

