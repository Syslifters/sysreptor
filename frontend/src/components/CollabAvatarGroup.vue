<template>
  <span v-if="clientsAll.length > 0" class="avatar-group">
    <v-avatar 
      v-for="c in clientsVisible" 
      :key="c.client_id"
      size="small"
      density="compact"
      class="avatar-group-item"
    >
      {{ c.user.first_name?.[0] }}{{ c.user.last_name?.[0] }}
      <s-tooltip activator="parent">
        {{ c.user.username }} <template v-if="c.user.name">({{ c.user.name }})</template>
      </s-tooltip>
    </v-avatar>
    <v-avatar 
      v-if="clientsHidden.length > 0"
      size="small"
      density="compact"
      class="avatar-group-item"
    >
      +{{ clientsHidden.length }}
      <s-tooltip activator="parent">
        <span v-for="c in clientsHidden" :key="c.client_id">
          {{ c.user.username }} <template v-if="c.user.name">({{ c.user.name }})</template><br>
        </span>
      </s-tooltip>
    </v-avatar>
  </span>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  collab: CollabPropType;
  limit?: number;
}>(), {
  limit: 3,
});
const clientsAll = computed(() => props.collab.clients);
const clientsVisible = computed(() => clientsAll.value.slice(0, clientsAll.value.length > props.limit ? props.limit - 1 : undefined));
const clientsHidden = computed(() => clientsAll.value.length > props.limit ? clientsAll.value.slice(props.limit - 1) : []);
</script>

<style lang="scss" scoped>
.avatar-group {
  line-height: 1rem;
}
.avatar-group-item {
  font-size: small;
  background-color: rgb(var(--v-theme-secondary));
  color: rgb(var(--v-theme-on-secondary));
  border: 1px solid rgb(var(--v-theme-on-secondary), 0.75);

  /* overlap */
  margin-right: -12px;
  &:last-of-type {
    margin-right: 0;
  }

  /* hover animation */
  transition: all .2s ease-out;
  &:hover {
    z-index: 1;
    transform: translateY(-4px);
  }
}
</style>
