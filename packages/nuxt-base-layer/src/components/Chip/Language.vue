<template>
  <v-chip class="ma-1" size="small">
    <v-icon size="small" start icon="mdi-translate" />
    {{ languageInfo.name }}
    <v-icon 
      v-if="props.filterable" 
      size="small" 
      end 
      icon="mdi-filter-variant" 
      @click.stop.prevent="applyFilter"
      class="ml-1 filter-icon"
    />
  </v-chip>
</template>

<script setup lang="ts">
const props = defineProps<{
  value: string;
  filterable?: boolean;
}>();

const emit = defineEmits<{
  filter: [filter: FilterValue];
}>();

const apiSettings = useApiSettings();
const languageInfo = computed(() => apiSettings.settings!.languages.find(l => l.code === props.value) || { code: '??-??', name: 'Unknown' });

function applyFilter() {
  emit('filter', {
    id: 'language',
    value: props.value,
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
