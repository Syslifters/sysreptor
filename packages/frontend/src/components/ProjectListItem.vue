<template>
  <v-list-item 
    :to="`/projects/${props.item.id}/reporting/`" 
    lines="two"
    class="project-list-item"
  >
    <template #title>
      {{ props.item.name }}

      <div class="action-buttons d-inline-flex ml-2">
        <s-btn-icon
          :to="`/projects/${props.item.id}/`"
          @click.stop
          icon="mdi-cogs"
          size="x-small"
          v-tooltip="{ text: 'Settings', location: 'top', openDelay: 500 }"
        />
        <s-btn-icon
          :to="`/projects/${props.item.id}/reporting/`"
          @click.stop
          icon="mdi-text"
          size="x-small"
          v-tooltip="{ text: 'Reporting', location: 'top', openDelay: 500 }"
        />
        <s-btn-icon
          :to="`/projects/${props.item.id}/notes/`"
          @click.stop
          icon="mdi-notebook"
          size="x-small"
          v-tooltip="{ text: 'Notes', location: 'top', openDelay: 500 }"
        />
        <s-btn-icon
          :to="`/projects/${props.item.id}/publish/`"
          @click.stop
          icon="mdi-earth"
          size="x-small"
          v-tooltip="{ text: 'Publish', location: 'top', openDelay: 500 }"
        />
      </div>
    </template>

    <template #subtitle>
      <chip-created :value="props.item.created" />
      <chip-member
        v-for="user in props.item.members" 
        :key="user.id" 
        :value="user" 
        :filterable="true"
        @filter="emit('filter', $event)"
      />
      <chip-member 
        v-for="user in props.item.imported_members" 
        :key="user.id" 
        :value="user" 
        imported
      />
      <chip-tag 
        v-for="tag in props.item.tags" 
        :key="tag" 
        :value="tag" 
        :filterable="true"
        @filter="emit('filter', $event)"
      />
    </template>
  </v-list-item>
</template>

<script setup lang="ts">
const props = defineProps<{
  item: PentestProject;
}>();
const emit = defineEmits<{
  filter: [filter: FilterValue];
}>();
</script>

<style lang="scss" scoped>
.action-buttons {
  opacity: 0;
  transition: opacity 0.2s ease-in-out;
}
.project-list-item:hover {
  .action-buttons {
    opacity: 1;
  }
}
</style>
