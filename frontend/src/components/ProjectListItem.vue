<template>
  <v-list-item :to="`/projects/${props.item.id}/reporting/`" lines="two">
    <v-list-item-title>{{ props.item.name }}</v-list-item-title>

    <v-list-item-subtitle class="mt-1">
      <chip-created :value="props.item.created" />
      <chip-member v-for="user in props.item.members" :key="user.id" :value="user" />
      <chip-member v-for="user in props.item.imported_members" :key="user.id" :value="user" imported />
      <chip-tag v-for="tag in props.item.tags" :key="tag" :value="tag" />
    </v-list-item-subtitle>
  </v-list-item>
</template>

<script setup lang="ts">
const props = defineProps<{
  item: PentestProject
}>();
</script>
