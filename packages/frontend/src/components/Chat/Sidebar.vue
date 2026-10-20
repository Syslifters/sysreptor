<template>
  <div class="h-100 d-flex flex-column">
    <div class="sidebar-header">
      <div class="chat-header-row d-flex align-center">
        <v-tabs
          v-model="selectedTabId"
          density="compact"
          color="primary"
          align-tabs="start"
          show-arrows
          center-active
          class="chat-tabs flex-grow-1 align-self-stretch"
        >
          <v-tab
            v-for="tab in chatTabs.tabsState.value.tabs"
            :key="tab.id"
            :value="tab.id"
            slim
            class="chat-tab"
          >
            <template v-if="tabStatusColor(tab.id)" #prepend>
              <v-icon
                icon="mdi-circle-medium"
                size="12"
                :color="tabStatusColor(tab.id)"
              />
            </template>
            <span class="chat-tab-label text-truncate">{{ tabLabel(tab) }}</span>
            <template #append>
              <s-btn-icon
                icon="mdi-close"
                size="x-small"
                density="compact"
                class="chat-tab-close"
                @click.stop="closeTab(tab.id)"
              />
            </template>
          </v-tab>
        </v-tabs>
        <div class="chat-header-actions d-flex align-center flex-shrink-0">
          <s-btn-icon
            @click="newChat"
            icon="mdi-plus-circle"
            v-tooltip.top="'New agent (Ctrl+L)'"
            density="compact"
          />
          <s-btn-icon
            density="compact"
            v-tooltip.top="'Agent history'"
          >
            <v-icon icon="mdi-history" />
            <v-menu
              v-model="historyMenuOpen"
              activator="parent"
              location="bottom end"
              :close-on-content-click="true"
            >
              <v-list density="compact" min-width="260" max-width="320">
                <v-list-item v-if="historyLoading">
                  <template #prepend>
                    <v-progress-circular indeterminate size="16" width="2" class="mr-2" />
                  </template>
                  <v-list-item-title class="text-disabled">Loading...</v-list-item-title>
                </v-list-item>
                <template v-else>
                  <v-list-item
                    v-for="thread in historyThreads"
                    :key="thread.id"
                    @click="chatTabs.open({ threadId: thread.id, title: thread.title || '' })"
                  >
                    <v-list-item-title class="text-body-medium text-truncate">
                      {{ thread.title || 'New agent' }}
                    </v-list-item-title>
                    <v-list-item-subtitle class="text-body-small">
                      {{ formatThreadCreated(thread.created) }}
                    </v-list-item-subtitle>
                    <template #append>
                      <v-progress-circular
                        v-if="thread.run_status === 'running'"
                        indeterminate
                        size="14"
                        width="2"
                        class="mr-1"
                      />
                      <v-icon
                        v-else-if="historyStatusColor(thread.run_status)"
                        icon="mdi-circle-medium"
                        size="12"
                        :color="historyStatusColor(thread.run_status)"
                        class="mr-1"
                      />
                    </template>
                  </v-list-item>
                  <v-list-item v-if="historyThreads.length === 0" disabled>
                    <v-list-item-title class="text-disabled">No previous agents</v-list-item-title>
                  </v-list-item>
                </template>
              </v-list>
            </v-menu>
          </s-btn-icon>
          
          <s-btn-icon @click="sidebarType = ReportingSidebarType.NONE">
            <v-icon size="x-large" icon="mdi-close" />
          </s-btn-icon>
        </div>
      </div>
      <v-divider />
    </div>

    <chat-thread
      v-if="selectedTabId"
      :key="selectedTabId"
      ref="threadRef"
      class="flex-grow-height"
      :project="props.project"
      :tab-id="selectedTabId"
      :active="true"
      :context="props.context"
      :collab-flush="props.collabFlush"
      :readonly="props.readonly"
      :has-models-configured="hasModelsConfigured"
    />
  </div>
</template>

<script setup lang="ts">
import { formatDistanceToNow, parseISO } from 'date-fns';
import { parseCommentLocation, prettyFieldLabel } from '~/utils/comments';
import { useProjectAiChatTabs } from '@/utils/agent';

type HistoryThread = {
  id: string;
  title: string;
  run_status: string|null;
  created: string;
};

const props = defineProps<{
  project: PentestProject;
  projectType?: ProjectType;
  context: Record<string, string|undefined>;
  collabFlush?: (() => void|Promise<void>);
  readonly?: boolean;
}>();

const sidebarType = defineModel<ReportingSidebarType>('sidebarType', { required: true });

const localSettings = useLocalSettings();
const apiSettings = useApiSettings();
const projectStore = useProjectStore();
const chatTabs = useProjectAiChatTabs(props.project.id);

const hasModelsConfigured = computed(() => (apiSettings.settings?.ai_agent_models?.length || 0) > 0);

const selectedTabId = computed({
  get: () => chatTabs.tabsState.value.activeTabId,
  set: (tabId: string | null) => {
    if (tabId) {
      chatTabs.select(tabId);
    }
  },
});
const threadRef = useTemplateRef<any>('threadRef');

function tabLabel(tab: { id: string }) {
  const state = projectStore.data[props.project.id]?.aiAgentThreads[tab.id];
  return state?.title || 'New agent';
}

function tabStatusColor(tabId: string): string|undefined {
  const state = projectStore.data[props.project.id]?.aiAgentThreads[tabId];
  if (!state) {
    return undefined;
  }
  if (state.run || state.currentRequest) {
    return 'primary';
  }
  if (state.error) {
    return 'error';
  }
  if (state.interrupts?.length) {
    return 'info';
  }
  return undefined;
}

function historyStatusColor(status: string|null): string|undefined {
  if (status === 'interrupted') {
    return 'info';
  }
  if (status === 'error' || status === 'cancelled') {
    return 'error';
  }
  return undefined;
}

function closeTab(tabId: string) {
  if (chatTabs.close(tabId)) {
    sidebarType.value = ReportingSidebarType.NONE;
  }
}

async function newChat() {
  chatTabs.open();
  await nextTick();
  threadRef.value?.focus?.();
}
useKeyboardShortcut('ctrl+l', newChat);

const historyMenuOpen = ref(false);
const historyLoading = ref(false);
const historyThreads = ref<HistoryThread[]>([]);
async function refreshHistoryList() {
  historyLoading.value = true;
  try {
    const res = await $fetch<PaginatedResponse<HistoryThread>>('/api/v1/utils/chat/', {
      method: 'GET',
      query: { project: props.project.id },
    });
    historyThreads.value = res.results;
  } catch (error) {
    requestErrorToast({ error, message: 'Failed to load agent history' });
  } finally {
    historyLoading.value = false;
  }
}
whenever(historyMenuOpen, refreshHistoryList);

function formatThreadCreated(created: string) {
  try {
    return formatDistanceToNow(parseISO(created), { addSuffix: true });
  } catch {
    return created;
  }
}

async function onPrefillPrompt(event: any) {
  if (!hasModelsConfigured.value) {
    return;
  }

  let text = '';
  if (event.type === 'fill_field' && event.collabPath && props.projectType) {
    const relativePath = event.collabPath.split('/').at(-1) || event.collabPath;
    const location = parseCommentLocation(relativePath);
    const fieldId = location?.dataPath.replaceAll('.[', '[') || '';
    const fieldLabel = prettyFieldLabel(relativePath, props.projectType) || fieldId;

    let entityKind: string | undefined;
    let title: string | undefined;
    if (location?.type === 'findings') {
      entityKind = 'finding';
      const finding = projectStore.findings(props.project.id).find(f => f.id === location.id);
      title = finding?.data?.title || location.id;
    } else if (location?.type === 'sections') {
      entityKind = 'section';
      const section = projectStore.sections(props.project.id).find(s => s.id === location.id);
      title = section?.label || location.id;
    }

    if (entityKind && location) {
      text = `Draft or rewrite the "${fieldLabel}" (${fieldId}) field in ${entityKind} "${title}" (ID ${location.id}). ` +
        `Base the text on other fields in this ${entityKind} and project notes; do not invent facts. ` +
        'Ask the user if required information is missing. ' +
        'Update only this field.';
    }
  }
  if (!text) {
    return;
  }

  const tab = chatTabs.open();
  const state = chatTabs.ensureThread(tab.id);
  state.draftMessage = text;

  if (localSettings.reportingChatAgent !== 'project_agent' && apiSettings.isProfessionalLicense) {
    localSettings.reportingChatAgent = 'project_agent';
  }

  await nextTick();
  threadRef.value?.focus?.();
}
const eventBusPrefillPrompt = useEventBus('ai:prefillPrompt');
eventBusPrefillPrompt.on(onPrefillPrompt);
onBeforeUnmount(() => {
  eventBusPrefillPrompt.off(onPrefillPrompt);
  // Detach all streams for this project, do not cancel runs
  chatTabs.detachAll();
});
</script>

<style lang="scss" scoped>
.chat-header-row {
  min-width: 0;
}
.chat-header-actions-spacer {
  width: 0.25rem;
}
.chat-tabs {
  min-width: 0;
  height: auto;
}
.chat-tabs:deep() {
  .v-btn {
    text-transform: none;
    letter-spacing: normal;
    min-width: 0;
    height: 100%;
  }
}

.chat-tab-label {
  max-width: 7rem;
  display: inline-block;
}
</style>
