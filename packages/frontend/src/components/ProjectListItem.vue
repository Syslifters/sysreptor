<template>
  <v-list-item 
    :to="`/projects/${props.item.id}/reporting/`" 
    lines="two"
    class="project-list-item"
  >
    
    <v-list-item-title class="ms-2">
      {{ props.item.name }}
      <div class="action-buttons d-inline-flex ml-2">
        <v-tooltip location="top" text="Settings" open-delay="500">
          <template #activator="{ props: tooltipProps }">
            <v-btn
              v-bind="tooltipProps"
              variant="text"
              size="x-small"
              icon="mdi-cogs"
              :to="`/projects/${props.item.id}/`"
              @click.stop
            />
          </template>
        </v-tooltip>
        
        <v-tooltip location="top" text="Notes" open-delay="500">
          <template #activator="{ props: tooltipProps }">
            <v-btn
              v-bind="tooltipProps"
              variant="text"
              size="x-small"
              icon="mdi-notebook"
              :to="`/projects/${props.item.id}/notes/`"
              @click.stop
            />
          </template>
        </v-tooltip>
        <v-tooltip location="top" text="Publish" open-delay="500">
          <template #activator="{ props: tooltipProps }">
            <v-btn
              v-bind="tooltipProps"
              variant="text"
              size="x-small"
              icon="mdi-earth"
              :to="`/projects/${props.item.id}/publish/`"
              @click.stop
            />
          </template>
        </v-tooltip>
      </div>
    </v-list-item-title>

    <v-list-item-subtitle class="mt-1">
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
    </v-list-item-subtitle>
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
