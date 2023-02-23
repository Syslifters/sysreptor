<template>
  <list-view url="/projecttypes/?public=true&ordering=name">
    <template #title>Report Designs</template>
    <template #actions v-if="$auth.hasScope('designer')">
      <create-design-dialog />
      <btn-import :import="performImport" />
    </template>
    <template #item="{item}">
      <v-list-item :to="`/designs/${item.id}/pdfdesigner/`" nuxt>
        <v-list-item-title>
          {{ item.name }}
        </v-list-item-title>
      </v-list-item>
    </template>
  </list-view>
</template>

<script>
import { uploadFileHelper } from '~/utils/upload';

export default {
  head: {
    title: 'Designs',
  },
  methods: {
    async performImport(file) {
      const designs = await uploadFileHelper(this.$axios, '/projecttypes/import/', file);
      this.$router.push({ path: `/designs/${designs[0].id}/` });
    },
  }
}
</script>
