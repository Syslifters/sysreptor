<template>
  <v-list-item :to="`/projects/${item.id}/reporting/`" nuxt two-line>
    <v-list-item-content>
      <v-list-item-title>
        {{ item.name }}
      </v-list-item-title>
            
      <v-list-item-subtitle>
        <v-chip v-for="user in item.members" :key="user.id" class="ma-1 mt-2" small>
          {{ user.username }}
        </v-chip>
        <v-chip v-for="user in item.imported_members" :key="user.id" class="ma-1 mt-2" small>
          {{ user.name }} (imported)
        </v-chip>
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
