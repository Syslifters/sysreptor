import {gfmStrikethrough} from 'micromark-extension-gfm-strikethrough';
import {gfmStrikethroughFromMarkdown, gfmStrikethroughToMarkdown} from 'mdast-util-gfm-strikethrough';
import { addRemarkExtension } from './helpers';


export function remarkStrikethrough() {
  addRemarkExtension(this, gfmStrikethrough(), gfmStrikethroughFromMarkdown, gfmStrikethroughToMarkdown);
}

