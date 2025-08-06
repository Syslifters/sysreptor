<template>
  <v-list-item 
    :to="`/designs/${item.id}/pdfdesigner/`" 
    lines="two" 
    :data-testid="`design-${item.id}`"
    class="design-list-item"
  >
    <template #title>
      {{ title }}

      <div v-if="actionButtons" class="action-buttons d-inline-flex ml-2">
        <s-btn-icon
          :to="`/designs/${item.id}/`"
          @click.stop
          icon="mdi-cogs"
          size="x-small"
          v-tooltip="{ text: 'Settings', location: 'top', openDelay: 500 }"
        />
        <s-btn-icon
          :to="`/designs/${item.id}/pdfdesigner/`"
          @click.stop
          icon="mdi-pencil-ruler"
          size="x-small"
          v-tooltip="{ text: 'PDF Designer', location: 'top', openDelay: 500 }"
        />
        <s-btn-icon
          :to="`/designs/${item.id}/reportfields/`"
          @click.stop
          icon="mdi-alpha-r-box"
          size="x-small"
          v-tooltip="{ text: 'Report Fields', location: 'top', openDelay: 500 }"
        />
        <s-btn-icon
          :to="`/designs/${item.id}/findingfields/`"
          @click.stop
          icon="mdi-alpha-f-box"
          size="x-small"
          v-tooltip="{ text: 'Finding Fields', location: 'top', openDelay: 500 }"
        />
        <s-btn-icon
          :to="`/designs/${item.id}/notes/`"
          @click.stop
          icon="mdi-notebook"
          size="x-small"
          v-tooltip="{ text: 'Notes', location: 'top', openDelay: 500 }"
        />
      </div>
    </template>

    <template #subtitle>
      <chip-status
        v-if="item.status"
        :value="item.status"
        :filterable="true"
        @filter="emit('filter', $event)"
      />
      <chip-language
        v-if="item.language"
        :value="item.language"
        :filterable="true"
        @filter="emit('filter', $event)"
      />
      <chip-tag
        v-for="tag in props.item.tags || []"
        :key="tag"
        :value="tag"
        :filterable="true"
        @filter="emit('filter', $event)"
      />
    </template>
  </v-list-item>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { formatProjectTypeTitle } from '@base/composables/projecttype';
import type { ProjectType } from '@base/utils/types';

const props = defineProps<{
  item: ProjectType;
  formatTitle?: boolean;
  actionButtons?: boolean;
}>();
const emit = defineEmits<{
  filter: [filter: FilterValue];
}>();

const title = computed(() => {
  if (props.formatTitle) {
    return formatProjectTypeTitle(props.item);
  } else {
    return props.item.name;
  }
})

</script>

<style lang="scss" scoped>
.action-buttons {
  opacity: 0;
  transition: opacity 0.2s ease-in-out;
}
.design-list-item:hover {
  .action-buttons {
    opacity: 1;
  }
}
</style>
