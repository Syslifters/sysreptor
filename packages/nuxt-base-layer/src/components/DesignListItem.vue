<template>
  <v-list-item :to="`/designs/${item.id}/pdfdesigner/`" :title="title" lines="two" :data-testid="`design-${item.id}`">
    <v-list-item-subtitle>
      <chip-review-status v-if="item.status" :value="item.status" />
      <chip-language v-if="item.language" :value="item.language" />
      <chip-tag v-for="tag in props.item.tags || []" :key="tag" :value="tag" />
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
const title = computed(() => {
  if (props.formatTitle) {
    return formatProjectTypeTitle(props.item);
  } else {
    return props.item.name;
  }
})
</script>
