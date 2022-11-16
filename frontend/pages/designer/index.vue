<template>
  <list-view url="/projecttypes/">
    <template #title>Report Designs</template>
    <template #actions v-if="$auth.hasScope('designer')">
      <create-design-dialog />
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
import CreateDesignDialog from '~/components/CreateDesignDialog.vue';
import { uploadFile } from '~/utils/upload';

export default {
  components: { CreateDesignDialog },
  methods: {
    async performImport(file) {
      const designs = await uploadFile(this.$axios, '/projecttypes/import/', file);
      this.$router.push({ path: `/designer/${designs[0].id}/` });
    },
  }
}
</script>
