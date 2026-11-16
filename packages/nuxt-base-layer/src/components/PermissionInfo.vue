<template>
  <span v-if="!hasPermission" class="permission-info" @click.prevent>
    <slot />
    <v-tooltip activator="parent" :text="text" />
  </span>
  <span v-else><slot /></span>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  value?: boolean|null;
  text?: string;
  permission?: UserPermission;
  permissionName?: string;
}>(), {
  value: null,
  text: undefined,
  permission: undefined,
  permissionName: undefined,
});

const auth = useAuth();
const apiSettings = useApiSettings();

const hasPermission = computed(() => {
  if (props.value === null) {
    if (props.permission) {
      return auth.hasPermission(props.permission);
    }
    return false;
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
