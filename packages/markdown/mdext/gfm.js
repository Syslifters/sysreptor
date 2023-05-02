import { gfmStrikethrough } from 'micromark-extension-gfm-strikethrough';
import { gfmStrikethroughFromMarkdown, gfmStrikethroughToMarkdown } from 'mdast-util-gfm-strikethrough';
import { gfmTaskListItem } from 'micromark-extension-gfm-task-list-item';
import { gfmTaskListItemFromMarkdown, gfmTaskListItemToMarkdown } from 'mdast-util-gfm-task-list-item';
import { addRemarkExtension } from './helpers';


export function remarkStrikethrough() {
  addRemarkExtension(this, gfmStrikethrough(), gfmStrikethroughFromMarkdown, gfmStrikethroughToMarkdown);
}


export function remarkTaskListItem() {
  addRemarkExtension(this, gfmTaskListItem, gfmTaskListItemFromMarkdown, gfmTaskListItemToMarkdown);
}
