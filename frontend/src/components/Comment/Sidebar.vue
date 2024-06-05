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
          <v-btn icon variant="text" @click="localSettings.reportingCommentSidebarVisible = false">
            <v-icon size="x-large" icon="mdi-close" />
          </v-btn>
        </template>
      </v-list-item>
      <v-divider />
    </div>

    <!-- TODO: community edition: comments disabled, readonly project -->

    <div v-if="comments.length === 0">
      <v-list-item title="No comments yet" />
    </div>
    
    <v-list-item v-for="commentGroup, path in commentGroups" :key="path" class="pl-0 pr-0 pt-0">
      <v-list-subheader :title="prettyFieldLabel(path as string)" class="mt-0 mb-1" />
      
      <v-card 
        v-for="comment in commentGroup" :key="comment.id"
        :id="`comment-${comment.id}`"
        @click="selectComment(comment, { focus: 'field' })"
        :ripple="false"
        density="compact"
        class="ma-1"
        :class="{'comment-selected': selectedComment?.id === comment?.id}"
      >
        <!-- TODO: styles for resolved comments -->
        <comment-content 
          :model-value="comment"
          :update="(c) => projectStore.updateComment(props.project, c)"
          :delete="() => projectStore.deleteComment(props.project, comment)"
          :readonly="props.readonly"
        >
          <template #menu>
            <btn-confirm
              :action="() => projectStore.resolveComment(props.project, comment, { status: comment.status === CommentStatus.OPEN ? CommentStatus.RESOLVED : CommentStatus.OPEN })"
              :disabled="props.readonly"
              :confirm="false"
              button-variant="icon"
              button-icon="mdi-check"
              button-text="Resolve"
              tooltip-text="Resolve comment"
              :button-color="'success'"
              density="compact"
            />
          </template>
        </comment-content>
        <div v-for="answer in comment.answers" :key="answer.id" class="ml-4">
          <v-divider />
          <comment-content 
            :model-value="answer"
            :update="a => projectStore.updateCommentAnswer(props.project, comment, a)"
            :delete="() => projectStore.deleteCommentAnswer(props.project, comment, answer)"
            :readonly="props.readonly"
          />
          <!-- TODO: create answer -->
        </div>
      </v-card>
      <v-divider class="mt-2" />
    </v-list-item>
  </v-navigation-drawer>
</template>

<script setup lang="ts">
import groupBy from 'lodash/groupBy';
import { type Comment, type FieldDefinition } from '@/utils/types';

export type CommentPropType = {
  comments: Comment[];
  selected: Comment|null;
};

const localSettings = useLocalSettings();
const projectStore = useProjectStore();

const props = defineProps<{
  readonly: boolean;
  project: PentestProject;
  projectType: ProjectType;
  findingId?: string;
  sectionId?: string;
}>();

const comments = computed(() => projectStore.comments(props.project.id, { projectType: props.projectType, findingId: props.findingId, sectionId: props.sectionId }));
const commentGroups = computed(() => groupBy(comments.value, 'dataPath'));
const selectedComment = ref<Comment|null>(null);
const commentProps = computed(() => ({
  comments: comments.value,
  selected: selectedComment.value,
}));

function prettyFieldLabel(dataPath: string) {
  let definition: any|FieldDefinition = props.findingId ? props.projectType.finding_fields : props.sectionId ? props.projectType.report_fields : undefined;
  const pathParts = dataPath.replaceAll('[', '.[').split('.');
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
  }
});

async function selectComment(comment: Comment, options?: { focus?: string }) {
  selectedComment.value = comment;

  if (comment) {
    // Open comment sidebar
    localSettings.reportingCommentSidebarVisible = true;
    await nextTick();

    // Scroll to focussed element
    if (options?.focus === 'field') {
      const el = document.getElementById(`comment-ref-${comment.id}`) || document.getElementById(comment.dataPath || '');
      el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else if (options?.focus === 'comment') {
      const el = document.getElementById(`comment-${comment.id}`);
      el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }
}

async function onCommentEvent(event: any) {
  if (event.type === 'create' && !props.readonly) {
    // TODO: rebase with collabState.version (in API)
    const comment = await projectStore.createComment(props.project, event.comment);
    await selectComment(comment, { focus: 'comment' });
    comment.editEnabled = false;
  } else if (event.type === 'select') {
    await selectComment(event.comment, { focus: 'comment' });
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

.comment-selected {
  :deep(.v-card__overlay) {
    background-color: currentColor;
    opacity: var(--v-activated-opacity);
  }
}


</style>
