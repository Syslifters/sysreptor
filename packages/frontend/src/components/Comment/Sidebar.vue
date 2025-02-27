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
      <v-list-item class="pt-0 pb-0">
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
    <v-list-item v-else-if="commentsVisible.length === 0">
      <v-list-item-title v-if="localSettings.reportingCommentStatusFilter === 'open'">No open comments</v-list-item-title>
      <v-list-item-title v-else>No comments found</v-list-item-title>
    </v-list-item>
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
        :is-active="comment.id === selectedComment?.id"
        :is-new="comment.id === commentNew?.id"
      />

      <v-divider class="mt-2" />
    </v-list-item>
  </v-navigation-drawer>
</template>

<script setup lang="ts">
import { groupBy } from 'lodash-es';
import { CollabEventType, CommentStatus, type Comment, type FieldDefinition } from '#imports';

const props = defineProps<{
  project: PentestProject;
  projectType: ProjectType;
  findingId?: string;
  sectionId?: string;
  readonly?: boolean;
}>();

const localSettings = useLocalSettings();
const apiSettings = useApiSettings();
const projectStore = useProjectStore();
const eventBusBeforeApplySetValue = useEventBus('collab:beforeApplySetValue');

const reportingCollab = projectStore.useReportingCollab({ project: props.project, findingId: props.findingId, sectionId: props.sectionId });
const commentNew = ref<Comment|null>(null);
const commentsAll = computedThrottled(() => {
  return projectStore.comments(props.project.id, { projectType: props.projectType, findingId: props.findingId, sectionId: props.sectionId });
}, { throttle: 1000 });
const commentsVisible = computed(() => {
  const out = localSettings.reportingCommentSidebarVisible ?
    commentsAll.value.filter(c => localSettings.reportingCommentStatusFilter === 'all' ? true : c.status === localSettings.reportingCommentStatusFilter) :
    commentsAll.value.filter(c => c.status === CommentStatus.OPEN);
  if (commentNew.value && !out.some(c => c.id === commentNew.value?.id)) {
    out.push(commentNew.value);
  }
  return out;
});

const commentGroups = computed(() => groupBy(commentsVisible.value, 'path'));
const selectedComment = ref<Comment|null>(null);
const readonly = computed(() => props.readonly || !apiSettings.isProfessionalLicense);

function prettyFieldLabel(path: string) {
  let definition: FieldDefinition[]|FieldDefinition|undefined = props.findingId ? props.projectType.finding_fields : props.sectionId ? props.projectType.report_sections.find(s => s.id === props.sectionId)?.fields : undefined;
  const pathParts = path.split('.').slice(3);
  const pathLabels = [];
  for (const pp of pathParts) {
    let label = null;
    if (Array.isArray(definition)) {
      definition = definition.find(f => f.id === pp);
    } else if (pp.startsWith('[') && pp.endsWith(']') && definition?.items) {
      definition = definition?.items;
      label = pp;
    } else if (definition?.properties) {
      definition = definition.properties.find(f => f.id === pp);
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

async function selectComment(comment: Comment|null, options?: { focus?: string }) {
  if (selectedComment.value?.id === comment?.id) {
    return;
  }
  selectedComment.value = comment;

  if (comment) {
    // Update DOM
    await nextTick();

    // Scroll to focussed element
    if (options?.focus === 'comment') {
      const elComment = document.getElementById(`comment-${comment.id}`);
      elComment?.scrollIntoView({ behavior: 'smooth', block: 'center' });

      const elCommentInput = elComment?.querySelector('.comment-content textarea') as HTMLTextAreaElement|undefined;
      elCommentInput?.focus({ preventScroll: true });
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

async function createComment(comment: Partial<Comment>) {
  if (props.readonly || !apiSettings.isProfessionalLicense) {
    return null;
  }

  const path = comment.path || comment.collabPath?.split('/').at(-1)

  const commentCreated = new Promise<Comment>(resolve => {
    function onSetValue(event: any) {
      if (event.path?.split('/').at(-1)!.startsWith('comments.') && event.value?.path === path) {
        eventBusBeforeApplySetValue.off(onSetValue);
        resolve(event.value);
      }
    }

    eventBusBeforeApplySetValue.on(onSetValue);
  });

  reportingCollab.onCollabEvent({
    type: CollabEventType.CREATE,
    path: reportingCollab.storeState.apiPath + 'comments',
    value: {
      text: '',
      text_range: null,
      ...comment,
      path,
    },
  });
  return await commentCreated;
}

async function onCommentEvent(event: any) {
  if (event.openSidebar || event.type === 'create') {
    localSettings.reportingCommentSidebarVisible = true;
    await nextTick();
  }

  if (event.type === 'create' && !props.readonly && apiSettings.isProfessionalLicense) {
    try {
      commentNew.value = await createComment(event.comment);
      await selectComment(commentNew.value, { focus: 'comment' });
      commentNew.value = null;
    } catch (error) {
      requestErrorToast({ error })
    }
  } else if (event.type === 'select') {
    await selectComment(event.comment, { focus: 'comment' });
  }
}

defineExpose({
  onCommentEvent,
});

</script>

<style lang="scss" scoped>
@use "@base/assets/vuetify.scss" as vuetify;

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
