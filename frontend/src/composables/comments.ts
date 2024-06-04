import orderBy from 'lodash/orderBy';
import { type Comment, type PentestProject } from '@/utils/types';

export type CommentPropType = {
  comments: Comment[];
  selected: Comment|null;
};

export function useComments(options: { 
  collabState: any;
  project: PentestProject;
  projectType: ProjectType;
  findingId?: string;
  sectionId?: string;
}) {
  const localSettings = useLocalSettings();

  const comments = computed(() => {
    // Filter and sort comments
    let commentData = Object.values(options.collabState.data.comments as Comment[]).map(c => ({ 
      ...c, 
      dataPath: c.path.split('.').slice(3).join('.').replaceAll('.[', '['),
      collabPath: options.collabState.apiPath + c.path,
    } as Comment));
    if (options.findingId) {
      const basePath = `findings.${options.findingId}.data.`;
      commentData = orderBy(
        commentData.filter(c => c.path.startsWith(basePath)), 
        [(c) => {
          return options.projectType?.finding_field_order.indexOf(c.dataPath!.split('.')?.[0])
        }, 'path', 'created']
      );
    } else if (options.sectionId) {
      const basePath = `sections.${options.sectionId}.data.`;
      commentData = orderBy(
        commentData.filter(c => c.path.startsWith(basePath)),
        [(c) => {
          const sectionFields = options.projectType?.report_sections.find(s => s.id === options.sectionId)?.fields || [];
          return sectionFields.indexOf(c.dataPath!.split('.')[0])
        }, 'path', 'created']
      );
    } else {
      commentData = [];
    }
    return commentData;
  });

  const selectedCommentId = ref<string|null>(null);
  const selectedComment = computed({
    get: () => comments.value.find(c => c.id === selectedCommentId.value) || null,
    set: (value: Comment|null) => {
      selectedCommentId.value = value?.id || null;
    }
  });

  async function selectComment(comment: Comment|null) {
    selectedComment.value = comment;

    if (comment) {
      // Open comment sidebar
      localSettings.reportingCommentSidebarVisible = true;
      await nextTick();
      // Scroll to comment in sidebar
      document.getElementById('comment-' + comment?.id)?.scrollIntoView({ behavior: 'instant', block: 'center' });

      // Scroll to field
      (document.getElementById('comment-ref-' + comment?.id) || document.getElementById(comment.dataPath || ''))?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  async function createComment(comment: Partial<Comment>) {
    let path = '';
    if (comment.path) {
      path = comment.path;
    } else if (comment.collabPath?.startsWith(options.collabState.apiPath)) {
      path = comment.collabPath.slice(options.collabState.apiPath.length);
    } else {
      throw new Error('Invalid comment path');
    }

    // TODO: create in API, rebase with collabState.version
    // TODO: select comment, make editable, focus text area
  }

  async function onCommentEvent(event: any) {
    if (event.type === 'create') {
      await createComment(event.comment);
    } else if (event.type === 'select') {
      await selectComment(event.comment);
    }
  }

  return {
    commentProps: computed<CommentPropType>(() => ({
      comments: comments.value,
      selected: selectedComment.value,
    })),
    selectedComment,
    onCommentEvent,
  };
}
