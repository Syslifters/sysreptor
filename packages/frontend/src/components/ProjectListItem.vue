<template>
  <v-list-item :to="`/projects/${props.item.id}/reporting/`" lines="two">
    <v-list-item-title>{{ props.item.name }}</v-list-item-title>

    <v-list-item-subtitle class="mt-1">
      <chip-created :value="props.item.created" />
      <chip-member
        v-for="user in props.item.members" 
        :key="user.id" 
        :value="user" 
        :filterable="true"
        @filter="$emit('filter', $event)"
      />
      <chip-member 
        v-for="user in props.item.imported_members" 
        :key="user.id" 
        :value="user" 
        imported
        :filterable="true"
        @filter="$emit('filter', $event)"
      />
      <chip-tag 
        v-for="tag in props.item.tags" 
        :key="tag" 
        :value="tag" 
        :filterable="true"
        @filter="$emit('filter', $event)"
      />
    </v-list-item-subtitle>
  </v-list-item>
</template>

<script setup lang="ts">
const props = defineProps<{
  item: PentestProject;
}>();

defineEmits<{
  filter: [filter: FilterValue];
}>();
</script>
