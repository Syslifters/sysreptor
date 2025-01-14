<template>
  <span v-if="!props.value" class="permission-info" @click.prevent>
    <slot />
    <s-tooltip activator="parent" :text="text" />
  </span>
  <span v-else><slot /></span>
</template>

<script setup lang="ts">
const props = defineProps<{
  value: boolean;
  text?: string;
  permissionName?: string;
}>();

const auth = useAuth();
const apiSettings = useApiSettings();

const text = computed(() => {
  if (props.text) {
    return props.text;
  } else if (auth.permissions.value.superuser && !auth.permissions.value.admin && apiSettings.isProfessionalLicense) {
    return 'Superuser permissions not enabled';
  } else if (props.permissionName) {
    return `Permission required: ${props.permissionName}`;
  } else {
    return 'No permission to perform this action';
  }
});

</script>

<style lang="scss" scoped>
.permission-info {
  pointer-events: auto;
}
</style>
