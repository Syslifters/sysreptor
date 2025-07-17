<template>
  <v-list-item 
    :to="`/designs/${item.id}/pdfdesigner/`" 
    lines="two" 
    :data-testid="`design-${item.id}`"
    class="design-list-item"
  >
    <v-list-item-title class="ms-2">
      {{ title }}
      <div class="action-buttons d-inline-flex ml-2">
        <v-tooltip location="top" text="Settings" open-delay="500">
          <template #activator="{ props: tooltipProps }">
            <v-btn
              v-bind="tooltipProps"
              variant="text"
              size="x-small"
              icon="mdi-cogs"
              :to="`/designs/${item.id}/`"
              @click.stop
            />
          </template>
        </v-tooltip>
        
        <v-tooltip location="top" text="Report Fields" open-delay="500">
          <template #activator="{ props: tooltipProps }">
            <v-btn
              v-bind="tooltipProps"
              variant="text"
              size="x-small"
              icon="mdi-alpha-r-box"
              :to="`/designs/${item.id}/reportfields/`"
              @click.stop
            />
          </template>
        </v-tooltip>
        
        <v-tooltip location="top" text="Finding Fields" open-delay="500">
          <template #activator="{ props: tooltipProps }">
            <v-btn
              v-bind="tooltipProps"
              variant="text"
              size="x-small"
              icon="mdi-alpha-f-box"
              :to="`/designs/${item.id}/findingfields/`"
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
              :to="`/designs/${item.id}/notes/`"
              @click.stop
            />
          </template>
        </v-tooltip>
      </div>
    </v-list-item-title>

    <v-list-item-subtitle>
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
    </v-list-item-subtitle>
  </v-list-item>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { formatProjectTypeTitle } from '@base/composables/projecttype';
import type { ProjectType } from '@base/utils/types';

const props = defineProps<{
  item: ProjectType;
  formatTitle?: boolean;
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
