<template>
  <v-chip class="ma-1" size="small">
    <v-icon size="small" start icon="mdi-translate" />
    {{ languageInfo.name.split('(')[0] }} ({{ languageInfo.code }})
  </v-chip>
</template>

<script setup lang="ts">
const props = defineProps<{
  value: string
}>();
const apiSettings = useApiSettings();
const languageInfo = computed(() => apiSettings.settings!.languages.find(l => l.code === props.value) || { code: '??-??', name: 'Unknown' });
</script>
