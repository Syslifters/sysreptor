<template>
  <span v-if="!hasPermission" class="permission-info" @click.prevent>
    <slot />
    <v-tooltip activator="parent" :text="text" />
  </span>
  <span v-else><slot /></span>
</template>

<script setup lang="ts">
const props = defineProps<{
  value?: boolean;
  text?: string;
  permission?: UserPermission;
  permissionName?: string;
}>();

const auth = useAuth();
const apiSettings = useApiSettings();

const hasPermission = computed(() => {
  if (props.value === undefined && props.permission) {
    return auth.hasPermission(props.permission);
  }
  return props.value;
})

const text = computed(() => {
  if (props.text) {
    return props.text;
  } else if (auth.permissions.value.superuser && !auth.permissions.value.admin && apiSettings.isProfessionalLicense) {
    return 'Superuser permissions not enabled';
  } else if (props.permissionName) {
    return `Permission required: ${props.permissionName}`;
  } else if (props.permission) {
    return `Permission required: ${props.permission}`;
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
