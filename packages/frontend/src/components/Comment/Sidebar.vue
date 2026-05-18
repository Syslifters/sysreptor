<template>
  <div>
    <div class="sidebar-header">
      <v-list-item class="pt-0 pb-0">
        <v-list-item-title class="text-title-large">
          <pro-info>Comments</pro-info>
        </v-list-item-title>
        <template #append>
          <s-btn-icon>
            <v-icon icon="mdi-filter-outline" />
            <v-menu activator="parent">
              <v-list 
                :selected="[statusFilter]" 
                @update:selected="statusFilter = $event?.[0] || 'all'"
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

          <v-btn icon variant="text" @click="localSettings.reportingSidebarType = ReportingSidebarType.NONE">
            <v-icon size="x-large" icon="mdi-close" />
          </v-btn>
        </template>
      </v-list-item>
      <v-divider />
    </div>

    <v-list-item v-if="!apiSettings.isProfessionalLicense">
      Comments are available<br>
      in SysReptor Professional.<br><br>
      See <a href="https://sysreptor.com/pricing" target="_blank" class="text-primary">https://sysreptor.com/pricing</a>
    </v-list-item>
    <v-list-item v-else-if="commentsVisible.length === 0">
      <v-list-item-title v-if="statusFilter === CommentStatus.OPEN">No open comments</v-list-item-title>
      <v-list-item-title v-else>No comments found</v-list-item-title>
    </v-list-item>
    <v-list-item v-else v-for="locationGroup in commentDisplayGroups" :key="locationGroup.locationKey" class="pl-0 pr-0 pt-0">
      <v-list-subheader
        v-if="isProjectWide"
        :tag="NuxtLink as any"
        :to="locationGroup.url"
        class="pl-2 mt-2 mb-1 text-title-medium location-subheader"
      >
        <span>{{ locationGroup.title }}</span>
      </v-list-subheader>

      <template v-for="fieldGroup in locationGroup.fieldGroups" :key="fieldGroup.path">
        <v-list-subheader class="pl-2 mt-1 mb-1">
          <span>{{ prettyFieldLabel(fieldGroup.path) }}</span>
          <s-btn-icon
            @click.stop="onCommentEvent({ type: 'create', comment: { path: fieldGroup.path } })"
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
          v-for="comment in fieldGroup.comments" :key="comment.id"
          :comment="comment"
          :project="props.project"
          :selectable-users="props.selectableUsers"
          @click="selectComment(comment, { focus: 'field' })"
          :is-active="comment.id === selectedComment?.id"
          :is-new="comment.id === commentNew?.id"
        />
        <v-divider class="mt-2" />
      </template>
    </v-list-item>
  </div>
</template>

<script setup lang="ts">
import { NuxtLink } from '#components';
import { CollabEventType, CommentStatus, ReportingSidebarType, type Comment, type FieldDefinition } from '#imports';
import {
  commentFieldDefinitions,
  commentLocationUrl,
  groupCommentsByLocation,
  isOnCommentLocationRoute,
  parseCommentLocation,
} from '~/utils/comments';

const props = defineProps<{
  project: PentestProject;
  projectType: ProjectType;
  findingId?: string;
  sectionId?: string;
  readonly?: boolean;
  selectableUsers?: UserShortInfo[];
}>();

const router = useRouter();
const localSettings = useLocalSettings();
const apiSettings = useApiSettings();
const projectStore = useProjectStore();
const eventBusBeforeApplySetValue = useEventBus('collab:beforeApplySetValue');

const reportingCollab = projectStore.useReportingCollab({ project: props.project });
const commentNew = ref<Comment|null>(null);
const commentsAll = computedList<Comment>(() => {
  return projectStore.comments(props.project.id, { projectType: props.projectType, findingId: props.findingId, sectionId: props.sectionId });
}, c => c.id);
const statusFilter = ref<CommentStatus|'all'>(CommentStatus.OPEN);
const commentsVisible = computed(() => {
  const out = localSettings.reportingSidebarType === ReportingSidebarType.COMMENTS ?
    commentsAll.value.filter(c => statusFilter.value === 'all' ? true : c.status === statusFilter.value) :
    commentsAll.value.filter(c => c.status === CommentStatus.OPEN);
  if (commentNew.value && !out.some(c => c.id === commentNew.value?.id)) {
    out.push(commentNew.value);
  }
  return out;
});

const isProjectWide = computed(() => !props.findingId && !props.sectionId);
const commentDisplayGroups = computed(() => groupCommentsByLocation(commentsVisible.value, {
  projectId: props.project.id,
  sections: projectStore.sections(props.project.id, { projectType: props.projectType }),
  findings: projectStore.findings(props.project.id, { projectType: props.projectType }),
}));
const selectedComment = ref<Comment|null>(null);
const readonly = computed(() => props.readonly || !apiSettings.isProfessionalLicense);

function prettyFieldLabel(path: string) {
  const location = parseCommentLocation(path);
  if (!location) {
    return '';
  }
  let definition: FieldDefinition[]|FieldDefinition|undefined = commentFieldDefinitions(props.projectType, location);
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

async function waitForElement(getElement: () => HTMLElement|null, maxAttempts = 20): Promise<HTMLElement|null> {
  for (let i = 0; i < maxAttempts; i++) {
    const el = getElement();
    if (el) {
      return el;
    }
    await nextTick();
  }
  return null;
}

async function selectComment(comment: Comment|null, options?: { focus?: string }) {
  if (selectedComment.value?.id === comment?.id) {
    return;
  }
  selectedComment.value = comment;

  if (comment) {
    const targetUrl = commentLocationUrl(props.project.id, comment.path);
    if (targetUrl) {
      if (!isOnCommentLocationRoute(router.currentRoute.value.path, targetUrl)) {
        await navigateTo(targetUrl);
      }
    }
    // Update DOM
    await nextTick();

    // Scroll to focussed element
    if (options?.focus === 'comment') {
      const elComment = await waitForElement(() => document.getElementById(`comment-${comment.id}`));
      elComment?.scrollIntoView({ behavior: 'smooth', block: 'center' });

      const elCommentInput = elComment?.querySelector('.comment-content *[contenteditable="true"]') as HTMLDivElement|undefined;
      elCommentInput?.focus({ preventScroll: true });
    } else if (options?.focus === 'field') {
      const fieldId = comment.path.split('.').slice(3).join('.').replaceAll('.[', '[');
      const elField = await waitForElement(() => document.getElementById(fieldId));

      const elFieldInput = (elField?.querySelector('*[contenteditable]') || elField?.querySelector('input')) as HTMLInputElement|undefined;
      const elCommentTextRange = await waitForElement(() => document.getElementById(`comment-textrange-${comment.id}`));

      (elCommentTextRange ?? elField)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      elFieldInput?.focus({ preventScroll: true });

      if (elFieldInput && elCommentTextRange && comment.text_range) {
        const range = document.createRange();
        range.selectNode(elCommentTextRange);
        range.setStart(elCommentTextRange, 0);
        range.setEnd(elCommentTextRange, 0);

        const selection = document.getSelection();
        selection?.removeAllRanges();
        selection?.addRange(range);
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
const eventBusComment = useEventBus('collab:commentEvent');
eventBusComment.on(onCommentEvent);
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

.location-subheader {
  text-decoration: none;

  &:hover {
    color: rgb(var(--v-theme-primary));
  }
}
</style>
