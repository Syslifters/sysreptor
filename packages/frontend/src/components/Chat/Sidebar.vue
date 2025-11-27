<template>
  <div class="h-100 d-flex flex-column">
    <div class="sidebar-header">
      <v-list-item class="pt-0 pb-0">
        <v-list-item-title class="text-h6">
          <v-badge content="Beta" color="primary" :offset-y="2" :offset-x="-10">
            AI Chat
          </v-badge>
        </v-list-item-title>
        <template #append>
          <s-btn-icon
            @click="agent.reset()"
            density="compact"
          >
            <v-icon icon="mdi-plus-circle" />
            <s-tooltip activator="parent" text="New chat (Ctrl+L)" />
          </s-btn-icon>

          <v-btn icon variant="text" @click="localSettings.reportingSidebarType = ReportingSidebarType.NONE">
            <v-icon size="x-large" icon="mdi-close" />
          </v-btn>
        </template>
      </v-list-item>
      <v-divider />
    </div>
    <div 
      ref="messagesContainerRef" 
      class="flex-grow-height overflow-y-auto pa-2"
      v-mutate.sub.child.char="() => syncScroll()"
      @scroll="onScrollMessages()"
    >
      <template v-for="msg in agent.messageHistory.value" :key="msg.id">
        <chat-ai-message
          v-if="msg.role === MessageRole.ASSISTANT && msg.reasoning"
          :msg="msg"
        />
        <chat-tool-call
          v-else-if="msg.role === MessageRole.TOOL && msg.tool_call"
          :value="msg.tool_call"
          :project="props.project"
        />
        <s-card v-else-if="msg.role === MessageRole.USER" variant="tonal">
          <v-card-text class="message-text">
            {{ msg.text }}
          </v-card-text>
        </s-card>
      </template>
    </div>
    <div class="pa-2">
      <s-card density="compact" variant="tonal">
        <v-textarea 
          v-model="form.message"
          :readonly="agent.inProgress.value"
          placeholder="Type a message..."
          variant="solo"
          density="compact"
          flat
          rows="1"
          max-rows="8"
          auto-grow
          hide-details="auto"
          spellcheck="false"
          autofocus
          class="textarea-message"
          :class="{'generating': agent.inProgress.value}"
        >
          <template #append-inner>
            <s-btn-icon
              v-if="!agent.inProgress.value"
              @click="sendMessage"
              :disabled="!form.message.trim()"
              icon="mdi-send"
              size="small"
              density="compact"
            >
              <v-icon icon="mdi-send" />
              <s-tooltip activator="parent" text="Send message (Ctrl+Enter)" />
            </s-btn-icon>
            <div v-else class="btn-stop" style="position: relative; display: inline-flex;">
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
              <s-tooltip activator="parent" text="Cancel" />
            </div>
          </template>
          <template #details>
            <div>
              <v-select
                v-model="localSettings.reportingChatAgent"
                :items="[
                  { value: 'project_ask', title: 'Ask', icon: 'mdi-comment-question-outline', proOnly: false },
                  { value: 'project_agent', title: 'Agent', icon: 'mdi-robot-outline', proOnly: true },
                ]"
                item-value="value"
                item-title="title"
                density="compact"
                variant="plain"
                hide-details
                class="select-agent"
              >
                <template #selection="{ item }">
                  <div class="d-flex align-center">
                    <v-icon :icon="item.raw.icon" size="x-small" class="mr-1" />
                    <span class="text-body-2">{{ item.raw.title }}</span>
                  </div>
                </template>
                <template #item="{ props: itemProps, item }">
                  <v-list-item 
                    v-bind="itemProps" 
                    density="compact"
                    :disabled="item.raw.proOnly && !apiSettings.isProfessionalLicense"
                  >
                    <template #prepend>
                      <v-icon :icon="item.raw.icon" />
                    </template>
                    <template #title>
                      <pro-info v-if="item.raw.proOnly">{{ item.raw.title }}</pro-info>
                      <span v-else>{{ item.raw.title }}</span>
                    </template>
                  </v-list-item>
                </template>
              </v-select>
            </div>
          </template>
        </v-textarea>
      </s-card>
      <div v-if="apiSettings.settings!.ai_agent_disclaimer" class="w-100 text-center text-body-2 text-disabled text-truncate">
        <i>{{ apiSettings.settings!.ai_agent_disclaimer }}</i>
        <s-tooltip activator="parent" :text="apiSettings.settings!.ai_agent_disclaimer" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { throttle } from 'lodash-es';

const props = defineProps<{
  project: PentestProject;
  projectType: ProjectType;
  context: Record<string, string|undefined>;
}>();


const localSettings = useLocalSettings();
const apiSettings = useApiSettings();
const projectStore = useProjectStore();
const reportingCollab = projectStore.useReportingCollab({ project: props.project, projectType: props.projectType });

const agent = projectStore.useReportingAgent({ project: props.project });
const messagesContainerRef = useTemplateRef('messagesContainerRef');
const isScrolledToBottom = ref(true);


const form = ref({
  message: '',
});
async function sendMessage() {
  // Flush collab events such that the server/agent has the latest data
  await reportingCollab.flushEvents();

  const promise = agent.submitMessage({ 
    message: form.value.message, 
    context: props.context,
    agent: localSettings.reportingChatAgent,
  });

  // Always scroll to bottom when sending a new message (after adding message to UI)
  await syncScroll({ force: true });

  const res = await promise;
  if (res === 'success') {
    // Clear message input on success. Else keep it for retry.
    form.value.message = '';
  }
}
useKeyboardShortcut('ctrl+enter', () => sendMessage());
useKeyboardShortcut('ctrl+l', () => agent.reset());


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
onMounted(async () => {
  syncScroll({ force: true });
  await agent.loadHistory();
});
const onScrollMessages = throttle(() => {
  if (!messagesContainerRef.value) {
    return;
  }
  const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.value;
  // Consider "at bottom" if within 100px of the bottom to account for rounding errors
  isScrolledToBottom.value = scrollHeight - scrollTop - clientHeight < 50;
}, 100);

</script>

<style lang="scss" scoped>
.message-text {
  white-space: pre-wrap;
  word-break: break-word;
}
.btn-stop {
  position: inherit;
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

.select-agent:deep() {
  .v-field {
    --v-input-control-height: 24px !important;
    --v-input-padding-top: 0;
  }
}
</style>
