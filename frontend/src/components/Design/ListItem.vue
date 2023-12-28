<template>
  <v-list-item :to="`/designs/${item.id}/pdfdesigner/`" :title="title" lines="two">
    <v-list-item-subtitle>
      <chip-review-status :value="item.status" />
      <chip-language :value="item.language" />
      <chip-tag v-for="tag in props.item.tags" :key="tag" :value="tag" />
    </v-list-item-subtitle>
  </v-list-item>
</template>

<script setup lang="ts">
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
