<template>
  <div class="text-body-medium text-disabled mt-2">
    <template v-if="props.value.name === 'get_finding_data' && props.project">
      <chat-tool-call-status :status="props.value.status" />
      Read finding
      <nuxt-link :to="`/projects/${props.project.id}/reporting/findings/${props.value.args.finding_id}/`">
        {{ getFindingTitle(props.value.args.finding_id, props.value.output?.title) }}
      </nuxt-link>
    </template>
    <template v-else-if="props.value.name === 'get_section_data' && props.project">
      <chat-tool-call-status :status="props.value.status" />
      Read section
      <nuxt-link :to="`/projects/${props.project.id}/reporting/sections/${props.value.args.section_id}/`">
        {{ getSectionTitle(props.value.args.section_id, props.value.output?.title) }}
      </nuxt-link>
    </template>
    <template v-else-if="props.value.name === 'get_note_data' && props.project">
      <chat-tool-call-status :status="props.value.status" />
      Read note
      <nuxt-link :to="`/projects/${props.project.id}/notes/${props.value.args.note_id}/`">
        {{ getNoteTitle(props.value.args.note_id, props.value.output?.title) }}
      </nuxt-link>
    </template>
    <template v-else-if="props.value.name === 'get_template_data'">
      <chat-tool-call-status :status="props.value.status" />
      Read template
      <nuxt-link :to="`/templates/${props.value.args.template_id}/`">
        {{ props.value.output?.title || props.value.args.template_id }}
      </nuxt-link>
    </template>
    <template v-else-if="['update_field_value', 'update_markdown_field'].includes(props.value.name) && props.project">
      <chat-tool-call-status :status="props.value.status" />
      Update
      <template v-if="props.value.args.path?.startsWith('findings.')">
        finding
        <nuxt-link :to="`/projects/${props.project.id}/reporting/findings/${props.value.args.path.split('.')[1]}/history/${props.value.timestamp}/`">
          {{ getFindingTitle(props.value.args.path.split('.')[1]) }}
        </nuxt-link>
      </template>
      <template v-else-if="props.value.args.path?.startsWith('sections.')">
        section
        <nuxt-link :to="`/projects/${props.project.id}/reporting/sections/${props.value.args.path.split('.')[1]}/history/${props.value.timestamp}/`">
          {{ getSectionTitle(props.value.args.path.split('.')[1]) }}
        </nuxt-link>
      </template>
    </template>
    <template v-else-if="props.value.name === 'list_templates'">
      <chat-tool-call-status :status="props.value.status" />
      List finding templates
      <span v-if="props.value.args.search_terms">matching "{{ props.value.args.search_terms }}"</span>
    </template>
    <template v-else-if="props.value.name === 'create_finding' && props.project">
      <chat-tool-call-status :status="props.value.status" />
      Create finding
      <nuxt-link :to="`/projects/${props.project.id}/reporting/findings/${props.value.output?.id}/`">
        {{ getFindingTitle(props.value.output?.id, props.value.output?.title) }}
      </nuxt-link>
    </template>
    <template v-else-if="props.value.name === 'write_todos'">
      <chat-tool-call-status :status="props.value.status" />
      Update TODO list
      <v-list 
        v-if="writeTodosList.length" 
        density="compact" 
        class="list-todos bg-transparent"
      >
        <v-list-item
          v-for="(todo, index) in writeTodosList"
          :key="index"
          :prepend-icon="todo.status === 'completed' ? 'mdi-checkbox-outline' : todo.status === 'in-progress' ? 'mdi-circle-box-outline' : 'mdi-checkbox-blank-outline'"
          class="text-body-medium min-h-0 py-1"
          :class="{ 'text-disabled': todo.status === 'completed' }"
        >
          <v-list-item-title class="text-body-medium">
            <span :class="{ 'text-decoration-line-through': todo.status === 'completed' }">{{ todo.content }}</span>
          </v-list-item-title>
        </v-list-item>
      </v-list>
    </template>
    <template v-else-if="props.value.name === 'task'">
      <chat-reasoning-panel
        :is-streaming="props.isStreaming"
        max-height-streaming="15em"
        class="subagent-messages border-l"
      >
        <template #title>
          <v-expansion-panel-title class="text-body-medium text-disabled">
            <chat-tool-call-status :status="props.value.status" class="mr-1" />
            Running subagent {{ props.value.args.subagent_type }}
          </v-expansion-panel-title>
        </template>
        <template #default>
          <chat-message
            v-if="props.value.subagentMessages?.length"
            v-for="msg, idx in props.value.subagentMessages" :key="msg.id"
            :msg="msg"
            :project="props.project"
            :is-streaming="props.isStreaming && idx === props.value.subagentMessages!.length - 1"
          />
          <markdown-preview
            v-if="props.value.content"
            :value="props.value.content"
            :throttle-ms="100"
            class="message-text"
          />
        </template>
      </chat-reasoning-panel>
    </template>
    <template v-else-if="['glob', 'grep'].includes(props.value.name)">
      <chat-tool-call-status :status="props.value.status" />
      {{ props.value.name }} "{{ props.value.args.pattern }}"
    </template>
    <template v-else-if="['read_file', 'write_file', 'edit_file'].includes(props.value.name)">
      <chat-tool-call-status :status="props.value.status" />
      {{ props.value.name }} {{ props.value.args.file_path }}
    </template>
    <template v-else-if="props.value.name === 'ls'">
      <chat-tool-call-status :status="props.value.status" />
      {{ props.value.name }} {{ props.value.args.path }}
    </template>
    <template v-else>
      <chat-tool-call-status :status="props.value.status" />
      {{ props.value.name }}
    </template>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  value: ToolCall;
  project?: PentestProject;
  isStreaming?: boolean;
}>();

const projectStore = useProjectStore();

function getFindingTitle(findingId: string, fallbackTitle?: string): string {
  const finding = projectStore.findings(props.project?.id || '').find(f => f.id === findingId);
  return finding?.data.title ?? fallbackTitle ?? findingId;
}
function getSectionTitle(sectionId: string, fallbackTitle?: string): string {
  const section = projectStore.sections(props.project?.id || '').find(s => s.id === sectionId);
  return section?.label ?? fallbackTitle ?? sectionId;
}
function getNoteTitle(noteId: string, fallbackTitle?: string): string {
  const note = projectStore.notes(props.project?.id || '').find(n => n.id === noteId);
  return note?.title ?? fallbackTitle ?? noteId;
}

const writeTodosList = computed(() => {
  if (props.value.name !== 'write_todos') {
    return [];
  }
  const todos = props.value?.args?.todos;
  if (!Array.isArray(todos)) {
    return [];
  }
  return todos.map((t: { content?: string; status?: string }) => ({
    content: typeof t.content === 'string' ? t.content : '',
    status: t.status,
  }));
});

</script>

<style lang="scss" scoped>
a {
  text-decoration: none;
  color: rgb(var(--v-theme-primary));
}

.list-todos:deep() {
  .v-list-item {
    min-height: 0;
    padding-top: 0;
    padding-bottom: 0;
  }
  .v-list-item__prepend .v-list-item__spacer {
    width: 0.5em;
  }
}

.subagent-messages:deep() {
  & > .v-expansion-panel > .v-expansion-panel-title {
    padding-left: 0;
  }
}

.message-text {
  font-size: 0.875rem;
}
</style>
