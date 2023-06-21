<template>
  <v-list-item :to="`/projects/${item.id}/reporting/`" nuxt two-line>
    <v-list-item-content>
      <v-list-item-title>
        {{ item.name }}
      </v-list-item-title>
            
      <v-list-item-subtitle class="mt-1">
        <chip-created :value="item.created" />
        <chip-member v-for="user in item.members" :key="user.id" :value="user" />
        <chip-member v-for="user in item.imported_members" :key="user.id" :value="user" imported />
        <chip-tag v-for="tag in item.tags" :key="tag" :value="tag" />
      </v-list-item-subtitle>
    </v-list-item-content>
  </v-list-item>
</template>

<script>
export default {
  props: {
    item: {
      type: Object,
      required: true,
    }
  }
}
</script>
