<template>
  <div v-if="clientsAll.length > 0" class="avatar-group">
    <user-avatar
      v-for="c in clientsVisible" 
      :key="c.client_id"
      :user="c.user"
      :color="c.client_color"
      class="avatar-group-item"
    >
      <s-tooltip activator="parent">
        <user-avatar :user="c.user" :color="c.client_color" />
        {{ userFullName(c) }}
      </s-tooltip>
    </user-avatar>
    <user-avatar
      v-if="clientsHidden.length > 0"
      :text="`+${clientsHidden.length}`"
      class="avatar-group-item"
    >
      <s-tooltip activator="parent">
        <span v-for="c in clientsHidden" :key="c.client_id">
          <user-avatar :user="c.user" :color="c.client_color" />
          {{ userFullName(c) }}
          <br />
        </span>
      </s-tooltip>
    </user-avatar>
  </div>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  collab?: CollabPropType;
  limit?: number;
}>(), {
  collab: undefined,
  limit: 3,
});
const clientsAll = computed(() => props.collab?.clients || []);
const clientsVisible = computed(() => clientsAll.value.slice(0, clientsAll.value.length > props.limit ? props.limit - 1 : undefined));
const clientsHidden = computed(() => clientsAll.value.length > props.limit ? clientsAll.value.slice(props.limit - 1) : []);

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
