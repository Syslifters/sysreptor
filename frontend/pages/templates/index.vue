<template>
  <list-view url="/findingtemplates/" :search="$route.query.search">
    <template #title>Finding Templates</template>
    <template #actions v-if="$auth.hasScope('template_editor')">
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
            <language-chip :value="item.language" />
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
export default {
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
