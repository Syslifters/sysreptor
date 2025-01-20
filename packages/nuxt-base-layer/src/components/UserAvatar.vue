<template>
  <v-avatar 
    :size="props.size"
    density="compact"
    class="collab-avatar-item"
    :style="{'--avatar-border-color': avatarColor}"
  >
    {{ avatarText }}<slot name="default" />
  </v-avatar>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  user?: UserShortInfo|null;
  text?: string;
  color?: string;
  size?: 'small'|'default'|'large';
}>(), {
  user: null,
  text: undefined,
  color: undefined,
  size: 'small',
});

const avatarText = computed(() => {
  if (props.text) {
    return props.text;
  } else {
    return (props.user?.username?.[0] || 'a').toLowerCase();
  }
});
const avatarColor = computed(() => {
  return props.color || props.user?.color || 'var(--v-theme-on-secondary)';
});
</script>

<style langs="scss" scoped>
.collab-avatar-item {
  background-color: rgb(var(--v-theme-secondary));
  color: rgb(var(--v-theme-on-secondary));
  border: 3px solid var(--avatar-border-color);
}

.v-avatar--size-small {
  font-size: small;
  border-width: 3px;
}
.v-avatar--size-default {
  font-size: 1.1em;
  border-width: 4px;
}
.v-avatar--size-large {
  font-size: 1.5em;
  border-width: 5px;
  font-weight: 600;
}
</style>

