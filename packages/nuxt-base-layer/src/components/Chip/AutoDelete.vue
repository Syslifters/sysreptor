<template>
  <chip-date
    :value="(props.value === 'never' || !apiSettings.isProfessionalLicense) ? null : props.value"
    icon="mdi-delete-clock"
    label="delete"
    tooltip-prefix-text="Automatic deletion: "
    relative="future"
    :color="isSoon ? 'error' : undefined"
  />
</template>

<script setup lang="ts">
import { isDeleteDateSoon } from '@base/utils/project';

const props = defineProps< {
  value: string|'never'|null,
}>();

const apiSettings = useApiSettings();

const isSoon = computed(() => isDeleteDateSoon(props.value));
</script>
