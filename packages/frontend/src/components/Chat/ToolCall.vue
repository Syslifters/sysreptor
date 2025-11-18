<template>
  <div class="text-body-2 text-disabled">
    <v-icon v-if="props.value.status === ToolCallStatus.SUCCESS" icon="mdi-check" color="success" />
    <v-icon v-else-if="props.value.status === ToolCallStatus.ERROR" icon="mdi-close" color="error" />
    <s-saving-loader-spinner v-else-if="props.value.status === ToolCallStatus.PENDING" />

    <template v-if="props.value.name === 'get_finding_data' && props.project">
      Read finding
      <nuxt-link :to="`/projects/${props.project.id}/reporting/findings/${props.value.args.finding_id}/`">
        {{ getFindingTitle(props.value.args.finding_id, props.value.output?.title) }}
      </nuxt-link>
    </template>
    <template v-else-if="props.value.name === 'get_section_data' && props.project">
      Read section
      <nuxt-link :to="`/projects/${props.project.id}/reporting/sections/${props.value.args.section_id}/`">
        {{ getSectionTitle(props.value.args.section_id, props.value.output?.title) }}
      </nuxt-link>
    </template>
    <template v-else-if="props.value.name === 'get_note_data' && props.project">
      Read note
      <nuxt-link :to="`/projects/${props.project.id}/notes/${props.value.args.note_id}/`">
        {{ getNoteTitle(props.value.args.note_id, props.value.output?.title) }}
      </nuxt-link>
    </template>
    <template v-else-if="props.value.name === 'get_template_data'">
      Read template
      <nuxt-link :to="`/templates/${props.value.args.template_id}/`">
        {{ props.value.output?.title || props.value.args.template_id }}
      </nuxt-link>
    </template>
    <template v-else-if="['update_field_value', 'update_markdown_field'].includes(props.value.name) && props.project">
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
      List finding templates
      <span v-if="props.value.args.search_terms">matching "{{ props.value.args.search_terms }}"</span>
    </template>
    <template v-else-if="props.value.name === 'create_finding' && props.project">
      Create finding
      <nuxt-link :to="`/projects/${props.project.id}/reporting/findings/${props.value.output?.id}/`">
        {{ getFindingTitle(props.value.output?.id, props.value.output?.title) }}
      </nuxt-link>
    </template>
    <template v-else>
      {{ props.value.name }}
    </template>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  value: ToolCall;
  project?: PentestProject;
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

</script>

<style lang="scss" scoped>
a {
  text-decoration: none;
  color: rgba(var(--v-theme-primary));
}

</style>
