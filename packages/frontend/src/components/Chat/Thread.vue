<template>
  <div class="h-100 d-flex flex-column">
    <div
      ref="messagesContainerRef"
      class="flex-grow-height overflow-y-auto pa-2"
      v-mutate.sub.child.char="() => syncScroll()"
      @scroll="onScrollMessages()"
    >
      <s-sidebar-empty-state
        v-if="!hasModelsConfigured"
        icon="mdi-creation-outline"
        title="No LLM models configured"
        text="Add LLM models in settings to use the agent."
        :action-text="auth.permissions.value.admin ? 'Open Settings' : undefined"
        to="/settings/"
      />
      <s-sidebar-empty-state
        v-else-if="agent.messageHistory.length === 0"
        icon="mdi-creation-outline"
        title="Start now with your agent"
        text="Ask about findings, draft text, or review the report."
      />
      <template v-else>
        <chat-message
          v-for="(msg, idx) in agent.messageHistory"
          :key="msg.id"
          :msg="msg"
          :project="props.project"
          :is-streaming="isChatMessageStreaming(msg, {
            inProgress: agent.inProgress,
            isLastMessage: idx === agent.messageHistory.length - 1,
          })"
          :is-last-message="isLastAssistantMessageInTurn(agent.messageHistory, idx)"
        />
        <template v-if="agent.interrupts.length > 0 && !agent.inProgress">
          <chat-interrupt-prompt
            v-for="interrupt in agent.interrupts"
            :key="interrupt.id"
            :interrupt="interrupt"
            @resume="onResume"
            class="mb-2"
          />
        </template>
      </template>
      <chat-reasoning-panel
        v-if="agent.inProgress && agent.messageHistory.at(-1)?.role === MessageRole.USER"
        :is-streaming="true"
      />

      <v-alert
        v-if="agent.error"
        type="error"
        variant="tonal"
        density="compact"
        class="mt-2 mb-2"
        :text="agent.error"
      />
    </div>
    <div class="pa-2">
      <s-card density="compact" variant="tonal" class="chat-compose-card">
        <chat-changes-panel
          v-if="apiSettings.isProfessionalLicense"
          :project="props.project"
          :changed-pages="runChangedPages"
          :readonly="props.readonly"
          @revert="onRevertPage"
          @accept="agent.acceptChange"
        />
        <v-textarea
          ref="messageTextareaRef"
          v-model="agent.draftMessage"
          :readonly="!hasModelsConfigured || agent.inProgress"
          @keypress="onKeyPress"
          placeholder="Type a message..."
          variant="solo"
          density="compact"
          flat
          rows="1"
          max-rows="5"
          auto-grow
          hide-details="auto"
          spellcheck="false"
          :autofocus="props.active"
          class="textarea-message"
          :class="{'generating': agent.inProgress}"
        >
          <template #append-inner>
            <s-btn-icon
              v-if="!agent.inProgress"
              @click="sendMessage"
              :disabled="!hasModelsConfigured || !agent.draftMessage.trim()"
              icon="mdi-send"
              size="small"
              density="compact"
              v-tooltip="'Send message (Enter)'"
            />
            <div v-else class="btn-stop">
              <v-progress-circular
                indeterminate
                :size="24"
                :width="2"
              />
              <s-btn-icon
                @click="agent.cancel()"
                icon="mdi-stop"
                size="small"
                density="compact"
              />
              <v-tooltip activator="parent" text="Cancel" />
            </div>
          </template>
          <template #details>
            <div class="d-flex align-center flex-wrap ga-2">
              <v-select
                v-model="selectedAgent"
                :items="[
                  { value: AiAgentMode.PROJECT_ASK, title: 'Ask', icon: 'mdi-comment-question-outline', proOnly: false },
                  { value: AiAgentMode.PROJECT_AGENT, title: 'Agent', icon: 'mdi-robot-outline', proOnly: true },
                ]"
                item-value="value"
                item-title="title"
                density="compact"
                variant="plain"
                hide-details
                class="select-agent"
              >
                <template #selection="{ item }">
                  <v-icon :icon="item.icon" size="x-small" class="mr-1" />
                  {{ item.title }}
                </template>
                <template #item="{ props: itemProps, item }">
                  <v-list-item
                    v-bind="itemProps"
                    density="compact"
                    :disabled="item.proOnly && !apiSettings.isProfessionalLicense"
                  >
                    <template #prepend>
                      <v-icon :icon="item.icon" />
                    </template>
                    <template #title>
                      <pro-info v-if="item.proOnly">{{ item.title }}</pro-info>
                      <span v-else>{{ item.title }}</span>
                    </template>
                  </v-list-item>
                </template>
              </v-select>
              <v-divider vertical class="select-divider" />
              <v-select
                v-model="selectedModel"
                :items="apiSettings.settings?.ai_agent_models || []"
                item-value="id"
                item-title="label"
                density="compact"
                variant="plain"
                hide-details="auto"
                placeholder="Model"
                persistent-placeholder
                no-data-text="No models available"
                class="select-model"
              />
            </div>
          </template>
        </v-textarea>
      </s-card>
      <div v-if="apiSettings.settings!.ai_agent_disclaimer" class="w-100 text-center text-body-medium text-disabled text-truncate">
        <i>{{ apiSettings.settings!.ai_agent_disclaimer }}</i>
        <v-tooltip activator="parent" :text="apiSettings.settings!.ai_agent_disclaimer" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { pick, throttle } from 'lodash-es';
import { getPageTitle, parseProjectFilePath, MessageRole, isChatMessageStreaming, isLastAssistantMessageInTurn, useProjectAiChatTab, type AgentChangedPage } from '@/utils/agent';

const props = defineProps<{
  project: PentestProject;
  tabId: string;
  active: boolean;
  context: Record<string, string|undefined>;
  collabFlush?: (() => void|Promise<void>);
  readonly?: boolean;
  hasModelsConfigured: boolean;
}>();

const apiSettings = useApiSettings();
const localSettings = useLocalSettings();
const auth = useAuth();
const projectStore = useProjectStore();

const agent = useProjectAiChatTab({ project: props.project, tabId: props.tabId });

const selectedAgent = computed({
  get: () => (agent.agent === AiAgentMode.PROJECT_AGENT && !apiSettings.isProfessionalLicense) ? AiAgentMode.PROJECT_ASK : agent.agent,
  set: (value: AiAgentMode) => { agent.agent = value; },
});
const selectedModel = computed({
  get: () => {
    const models = apiSettings.settings?.ai_agent_models || [];
    return models.find(m => m.id === agent.model)?.id
      ?? models.find(m => m.id === localSettings.reportingChatModel)?.id
      ?? models[0]?.id
      ?? null;
  },
  set: (value: string|null) => {
    agent.model = value;
    localSettings.reportingChatModel = value;
  },
});

const runChangedPages = computed(() => {
  const projectId = props.project.id;
  const titles = {
    findings: projectStore.findings(projectId),
    sections: projectStore.sections(projectId),
    notes: projectStore.notes(projectId),
  };

  return agent.changedFiles.flatMap((c) => {
    const fileRef = parseProjectFilePath(c.filePath);
    if (!fileRef) {
      return [];
    }
    return [{
      filePath: c.filePath,
      type: fileRef.type,
      id: fileRef.id,
      title: getPageTitle(fileRef, titles, c.title),
      isCreated: c.isCreated,
      diffTimestamp: c.diffTimestamp,
    } satisfies AgentChangedPage];
  });
});

async function onRevertPage(page: AgentChangedPage) {
  const fileRef = parseProjectFilePath(page.filePath);
  if (!fileRef || props.readonly) {
    return;
  }

  try {
    if (page.isCreated) {
      if (fileRef.type === 'finding') {
        await projectStore.deleteFinding(props.project, { id: fileRef.id });
      } else if (fileRef.type === 'note') {
        await projectStore.deleteNote(props.project, { id: fileRef.id });
      }
    } else if (fileRef.type === 'finding') {
      const historic = await $fetch<PentestFinding>(
        `/api/v1/pentestprojects/${props.project.id}/history/${page.diffTimestamp}/findings/${fileRef.id}/`,
      );
      await $fetch(`/api/v1/pentestprojects/${props.project.id}/findings/${fileRef.id}/`, {
        method: 'PATCH',
        body: pick(historic, ['data']),
      });
    } else if (fileRef.type === 'section') {
      const historic = await $fetch<ReportSection>(
        `/api/v1/pentestprojects/${props.project.id}/history/${page.diffTimestamp}/sections/${fileRef.id}/`,
      );
      await $fetch(`/api/v1/pentestprojects/${props.project.id}/sections/${fileRef.id}/`, {
        method: 'PATCH',
        body: pick(historic, ['data']),
      });
    } else if (fileRef.type === 'note') {
      const historic = await $fetch<ProjectNote>(
        `/api/v1/pentestprojects/${props.project.id}/history/${page.diffTimestamp}/notes/${fileRef.id}/`,
      );
      await $fetch(`/api/v1/pentestprojects/${props.project.id}/notes/${fileRef.id}/`, {
        method: 'PATCH',
        body: pick(historic, ['title', 'text', 'checked', 'icon_emoji']),
      });
    }

    agent.acceptChange(page.filePath);
  } catch (error) {
    requestErrorToast({
      error,
      message: page.isCreated ? 'Failed to delete page' : 'Failed to revert changes',
    });
  }
}

const messagesContainerRef = useTemplateRef('messagesContainerRef');
const messageTextareaRef = useTemplateRef('messageTextareaRef');
const isScrolledToBottom = ref(true);

async function sendMessage() {
  if (!props.hasModelsConfigured || !agent.draftMessage.trim()) {
    return;
  }

  await Promise.resolve(props.collabFlush?.());

  const message = agent.draftMessage;
  const promise = agent.submitMessage({
    message,
    context: props.context,
    agent: selectedAgent.value,
    model: selectedModel.value,
  });

  await syncScroll({ force: true });

  const res = await promise;
  if (res === 'success') {
    agent.draftMessage = '';
  }
}

function onResume(resumePayload: Record<string, any>) {
  agent.resume(resumePayload, {
    context: props.context,
    agent: selectedAgent.value,
    model: selectedModel.value,
  });
}

function onKeyPress(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

async function syncScroll(options?: { force?: boolean }) {
  if (options?.force) {
    isScrolledToBottom.value = true;
  }
  if (!messagesContainerRef.value || !isScrolledToBottom.value) {
    return;
  }
  await nextTick();
  messagesContainerRef.value!.scrollTop = messagesContainerRef.value!.scrollHeight;
}

const onScrollMessages = throttle(() => {
  if (!messagesContainerRef.value) {
    return;
  }
  const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.value;
  isScrolledToBottom.value = scrollHeight - scrollTop - clientHeight < 50;
}, 100);

watch(() => props.active, async (active, wasActive) => {
  if (active) {
    if (props.hasModelsConfigured && !wasActive) {
      await agent.refresh();
    }
    await syncScroll({ force: true });
    await nextTick();
    messageTextareaRef.value?.focus();
  }
}, { immediate: true });

defineExpose({
  focus: () => messageTextareaRef.value?.focus(),
  refresh: () => agent.refresh(),
  inProgress: computed(() => agent.inProgress),
  isEmpty: computed(() => !agent.threadId && agent.messageHistory.length === 0 && !agent.draftMessage.trim()),
});
</script>

<style lang="scss" scoped>
.btn-stop {
  position: relative;
  display: inline-flex;

  & > .v-progress-circular {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
  }
}

.textarea-message:deep() {
  textarea {
    font-size: 0.875rem;
  }
  .v-input__details {
    padding-top: 0;
  }
  .v-messages {
    display: none;
  }
}
.textarea-message.generating:deep() {
  textarea {
    opacity: var(--v-disabled-opacity);
  }
}

.select-agent:deep(), .select-model:deep() {
  min-width: 6rem;

  .v-field {
    --v-input-control-height: 24px;
    --v-input-padding-top: 0;
  }
  .v-field__input {
    font-size: 0.875rem;
  }
}
.select-divider {
  margin-top: 0.2rem;
  margin-bottom: 0.2rem;
}

.chat-compose-card:deep() {
  overflow: hidden;
}
</style>
