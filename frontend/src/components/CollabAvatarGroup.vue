<template>
  <div v-if="clientsAll.length > 0" class="avatar-group">
    <v-avatar 
      v-for="c in clientsVisible" 
      :key="c.client_id"
      size="small"
      density="compact"
      class="avatar-group-item"
      :style="{'--avatar-border-color': c.client_color}"
    >
      {{ userLetter(c) }}
      <s-tooltip activator="parent">
        <v-avatar size="small" density="compact" class="avatar-group-item avatar-colored" :style="{'--avatar-border-color': c.client_color}"> 
          {{ userLetter(c) }}
        </v-avatar>
        {{ userFullName(c) }}
      </s-tooltip>
    </v-avatar>
    <v-avatar 
      v-if="clientsHidden.length > 0"
      size="small"
      density="compact"
      class="avatar-group-item"
      :style="{'--avatar-border-color': 'var(--v-theme-on-secondary)'}"
    >
      +{{ clientsHidden.length }}
      <s-tooltip activator="parent">
        <span v-for="c in clientsHidden" :key="c.client_id">
          <v-avatar size="small" density="compact" class="avatar-group-item avatar-colored" :style="{'--avatar-border-color': c.client_color}"> 
            {{ userLetter(c) }}
          </v-avatar>
          {{ userFullName(c) }}<br>
        </span>
      </s-tooltip>
    </v-avatar>
  </div>
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

function userLetter(client: CollabPropType['clients'][0]) {
  return (client.user?.username[0] || 'a').toLowerCase();
}
function userFullName(client: CollabPropType['clients'][0]) {
  if (client.user) {
    return client.user.username + (client.user.name ? ` (${client.user.name})` : '');
  } else {
    return `${client.client_id} (Anonymous User)`;
  }
}
</script>

<style lang="scss" scoped>
.avatar-group {
  line-height: 1rem;
  display: flex;
  flex-direction: row;
}
.avatar-group-item {
  font-size: small;
  background-color: rgb(var(--v-theme-secondary));
  color: rgb(var(--v-theme-on-secondary));
  border: 3px solid var(--avatar-border-color);

  /* overlap */
  & {
    margin-right: -6px;
  }
  &:last-of-type {
    margin-right: 0;
  }

  /* hover animation */
  & {
    transition: all .2s ease-out;
  }
  &:hover {
    z-index: 1;
    transform: translateY(-4px);
  }
}
</style>
