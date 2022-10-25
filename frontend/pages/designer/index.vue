<template>
  <list-view url="/projecttypes/">
    <template #title>Report Designs</template>
    <template #actions v-if="$auth.hasScope('designer')">
      <s-btn @click="createProjectType" color="primary">
        <v-icon>mdi-plus</v-icon>
        Create new Report Design
      </s-btn>
      <btn-import :import="performImport" />
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
import { uploadFile } from '~/utils/upload';

export default {
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
    },
    async performImport(file) {
      const designs = await uploadFile(this.$axios, '/projecttypes/import/', file);
      this.$router.push({ path: `/designer/${designs[0].id}/` });
    },
  }
}
</script>
