<template>
  <list-view url="/projecttypes/">
    <template #title>Report Designs</template>
    <template #actions>
      <s-btn @click="createProjectType" color="primary">
        <v-icon>mdi-plus</v-icon>
        Create new Report Design
      </s-btn>
    </template>
    <template #item="{item}">
      <v-list-item :to="`/designer/${item.id}/pdfdesigner/`" nuxt>
        <v-list-item-title>
          {{ item.name }}
        </v-list-item-title>
      </v-list-item>
    </template>
  </list-view>
</template>

<script>
import ListView from '~/components/ListView.vue';

export default {
  components: { ListView },
  methods: {
    async createProjectType() {
      try {
        const obj = await this.$store.dispatch('projecttypes/create', {
          name: 'New Design',
        });
        this.$router.push(`/designer/${obj.id}`);
      } catch (error) {
        this.$toast.global.requestError({ error });
      }
    }
  }
}
</script>
