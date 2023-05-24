import { addRemarkExtension } from "./helpers";
import { labelEndSyntax } from "./label-end";


export function modifiedCommonmarkFeatures() {
  // Disable indented code blocks to not detect indented markdown as code blocks.
  addRemarkExtension(this, {disable: {null: ['codeIndented']}});

  // Override default labelEnd handler to support parsing nested labels in image captions and footnotes.
  addRemarkExtension(this, {disable: {null: ['labelEnd']}});
  addRemarkExtension(this, labelEndSyntax);
}