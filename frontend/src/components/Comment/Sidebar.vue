<template>
  <v-navigation-drawer
    v-if="localSettings.reportingCommentSidebarVisible"
    absolute
    permanent
    location="right"
    width="400"
    class="comment-sidebar"
  >
    <div class="sidebar-header">
      <v-list-item>
        <v-list-item-title class="text-h6">
          <pro-info>Comments</pro-info>
        </v-list-item-title>
        <template #append>
          <s-btn-icon>
            <v-icon icon="mdi-filter-variant" />
            <v-menu activator="parent">
              <v-list 
                :selected="[localSettings.reportingCommentStatusFilter]" 
                @update:selected="localSettings.reportingCommentStatusFilter = $event?.[0] || 'all'"
                mandatory
              >
                <v-list-item 
                  title="All"
                  :value="'all'"
                />
                <v-list-item
                  title="Open"
                  :value="CommentStatus.OPEN"
                />
              </v-list>
            </v-menu>
          </s-btn-icon>

          <v-btn icon variant="text" @click="localSettings.reportingCommentSidebarVisible = false">
            <v-icon size="x-large" icon="mdi-close" />
          </v-btn>
        </template>
      </v-list-item>
      <v-divider />
    </div>

    <v-list-item v-if="!apiSettings.isProfessionalLicense">
      Comments are available<br>
      in SysReptor Professional.<br><br>
      See <a href="https://docs.sysreptor.com/features-and-pricing/" target="_blank" class="text-primary">https://docs.sysreptor.com/features-and-pricing/</a>
    </v-list-item>
    <v-list-item v-else-if="commentsVisible.length === 0" title="No comments found" />
    <v-list-item v-else v-for="commentGroup, path in commentGroups" :key="path" class="pl-0 pr-0 pt-0">
      <v-list-subheader class="mt-1 mb-1">
        <span>{{ prettyFieldLabel(path as string) }}</span>
        <s-btn-icon
          @click="onCommentEvent({ type: 'create', comment: { path } })"
          :disabled="readonly"
          size="small"
          variant="flat"
          color="secondary"
          density="compact"
          class="ml-2"
        >
          <v-icon icon="mdi-plus" />
          <s-tooltip activator="parent" location="top">Add Comment</s-tooltip>
        </s-btn-icon>
      </v-list-subheader>
      
      <comment-detail
        v-for="comment in commentGroup" :key="comment.id"
        :comment="comment"
        :project="props.project"
        @click="selectComment(comment, { focus: 'field' })"
        :is-active="comment?.id === selectedComment?.id"
      />

      <v-divider class="mt-2" />
    </v-list-item>
  </v-navigation-drawer>
</template>

<script setup lang="ts">
import omit from 'lodash/omit';
import groupBy from 'lodash/groupBy';
import { CommentStatus, type Comment, type FieldDefinition } from '@/utils/types';

const localSettings = useLocalSettings();
const apiSettings = useApiSettings();
const projectStore = useProjectStore();

const props = defineProps<{
  project: PentestProject;
  projectType: ProjectType;
  findingId?: string;
  sectionId?: string;
  readonly?: boolean;
}>();

const commentsAll = computed(() => projectStore.comments(props.project.id, { projectType: props.projectType, findingId: props.findingId, sectionId: props.sectionId }));
const commentsVisible = computed(() => localSettings.reportingCommentSidebarVisible ?
  commentsAll.value.filter(c => localSettings.reportingCommentStatusFilter === 'all' ? true : c.status === localSettings.reportingCommentStatusFilter) :
  commentsAll.value.filter(c => c.status === CommentStatus.OPEN)
);

const commentGroups = computed(() => groupBy(commentsVisible.value, 'path'));
const selectedComment = ref<Comment|null>(null);
const commentProps = computed(() => ({
  comments: commentsVisible.value,
  selected: selectedComment.value,
}));
const readonly = computed(() => props.readonly || !apiSettings.isProfessionalLicense);

function prettyFieldLabel(path: string) {
  let definition: any|FieldDefinition = props.findingId ? props.projectType.finding_fields : props.sectionId ? props.projectType.report_fields : undefined;
  const pathParts = path.split('.').slice(3);
  const pathLabels = [];
  for (const pp of pathParts) {
    let label = null;
    if (pp.startsWith('[') && pp.endsWith(']')) {
      definition = definition?.items;
      label = pp;
    } else if (definition?.properties) {
      definition = definition.properties[pp];
    } else if (definition) {
      definition = definition?.[pp];
    }

    label = label || definition?.label;
    if (label) {
      pathLabels.push(label);
    }
  }

  return pathLabels.join(' / ');
}

watch(() => localSettings.reportingCommentSidebarVisible, (value) => {
  if (!value) {
    // Reset selected comment on sidebar close
    selectedComment.value = null;
  } else {
    // Reset show-all comments (incl. resolved)
    localSettings.reportingCommentStatusFilter = CommentStatus.OPEN;
  }
});

async function selectComment(comment: Comment|null, options?: { focus?: string, openSidebar?: boolean }) {
  if (selectedComment.value?.id === comment?.id) {
    return;
  }

  selectedComment.value = comment;

  if (comment) {
    // Open comment sidebar
    if (options?.openSidebar) {
      localSettings.reportingCommentSidebarVisible = true;
    }
    await nextTick();

    // Scroll to focussed element
    if (options?.focus === 'comment') {
      const elComment = document.getElementById(`comment-${comment.id}`);
      elComment?.scrollIntoView({ behavior: 'smooth', block: 'center' });

      const commentInput = elComment?.querySelector('.comment-content textarea') as HTMLTextAreaElement|undefined;
      commentInput?.focus({ preventScroll: true });
    } else if (options?.focus === 'field') {
      const filedId = comment.path.split('.').slice(3).join('.').replaceAll('.[', '[');
      const elField = document.getElementById(filedId);
      elField?.scrollIntoView({ behavior: 'smooth', block: 'center' });

      const elFieldInput = (elField?.querySelector('*[contenteditable]') || elField?.querySelector('input')) as HTMLInputElement|undefined;
      elFieldInput?.focus({ preventScroll: true });

      const elCommentTextRange = document.getElementById(`comment-textrange-${comment.id}`);
      if (elFieldInput && elCommentTextRange && comment.text_range) {
        const range = document.createRange();
        range.selectNode(elCommentTextRange);
        range.setStart(elCommentTextRange, 0);
        range.setEnd(elCommentTextRange, 0);

        const selection = document.getSelection();
        selection?.removeAllRanges();
        selection?.addRange(range)
      }
    }
  }
}

async function onCommentEvent(event: any) {
  if (event.type === 'create' && !props.readonly) {
    const comment = await projectStore.createComment(props.project, event.comment);
    await selectComment(comment, { focus: 'comment', openSidebar: true });
    comment.isNew = false;
  } else if (event.type === 'select') {
    await selectComment(event.comment, { focus: 'comment', ...omit(event, ['type', 'comment']) });
  }
}

defineExpose({
  commentProps,
  onCommentEvent,
});

</script>

<style lang="scss" scoped>
@use "@/assets/vuetify.scss" as vuetify;

.sidebar-header {
  position: sticky;
  top: 0;
  z-index: 10;
  background-color: vuetify.$navigation-drawer-background;
}

.v-list-subheader {
  min-height: 0;
}
</style>
