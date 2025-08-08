<template>
  <v-chip size="small" class="ma-1" :class="{'text-disabled': imported}">
    <template v-if="imported">
      <v-icon size="small" start class="text-disabled" icon="mdi-account-cancel" />
      {{ props.value.name }}
    </template>
    <template v-else>
      <v-icon size="small" start icon="mdi-account" />
      {{ props.value.username }}
    </template>

    <v-icon 
      v-if="props.filterable && props.value.username" 
      size="small" 
      end 
      icon="mdi-filter-variant" 
      @click.stop.prevent="applyFilter"
      class="ml-1 filter-icon"
    />

    <s-tooltip activator="parent" :disabled="!props.value.name">
      <span v-if="imported">{{ props.value.name }} (imported)</span>
      <span v-else>{{ props.value.name }}</span>
    </s-tooltip>
  </v-chip>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  value: UserShortInfo,
  imported?: boolean,
  filterable?: boolean,
}>(), {
  imported: false,
  filterable: false
});

const emit = defineEmits<{
  filter: [filter: FilterValue];
}>();

function applyFilter() {
  emit('filter', {
    id: 'member',
    value: props.value.username,
    exclude: false,
    regex: false
  });
}
</script>

<style lang="scss" scoped>
.filter-icon {
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.2s;
  
  &:hover {
    opacity: 1;
  }
}
</style>
