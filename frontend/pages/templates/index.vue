<template>
  <list-view url="/findingtemplates/" :search="$route.query.search" @update:search="$router.push({path: './', query: {search: $event}})">
    <template #title>Finding Templates</template>
    <template #actions>
      <s-btn @click="createTemplate" color="primary">
        <v-icon>mdi-plus</v-icon>
        Create new finding template
      </s-btn>
    </template>
    <template #item="{item}">
      <v-list-item :to="`/templates/${item.id}/`" nuxt two-line>
        <v-list-item-content>
          <v-list-item-title>
            <cvss-chip :value="item.data.cvss" />
            {{ item.data.title }}
          </v-list-item-title>
          <v-list-item-subtitle>
            <v-chip v-for="tag in item.tags" :key="tag" class="ma-1" small>
              {{ tag }}
            </v-chip>
          </v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
    </template>
  </list-view>
</template>

<script>
import ListView from '~/components/ListView.vue';
export default {
  components: { ListView },
  methods: {
    async createTemplate() {
      try {
        const template = await this.$store.dispatch('templates/create', {
          data: {
            title: 'New Finding Template',
          },
        });
        this.$router.push({ path: `/templates/${template.id}` });
      } catch (error) {
        this.$toast.global.requestError({ error });
      }
    }
  }
}
</script>
