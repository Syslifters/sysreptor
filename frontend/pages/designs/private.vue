<template>
  <div>
    <s-sub-menu>
      <v-tab :to="`/designs/`" nuxt exact>Global Designs</v-tab>
      <v-tab :to="`/designs/private/`" nuxt>Private Designs</v-tab>
    </s-sub-menu>

    <list-view url="/projecttypes/?scope=private&ordering=name">
      <template #title>Private Designs</template>
      <template #actions>
        <design-create-design-dialog project-type-scope="private" />
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
  </div>
</template>

<script>
import { uploadFileHelper } from '~/utils/upload';
export default {
  head: {
    title: 'Private Designs',
  },
  methods: {
    async performImport(file) {
      const designs = await uploadFileHelper(this.$axios, '/projecttypes/import/', file, { scope: 'private' });
      this.$router.push({ path: `/designs/${designs[0].id}/` });
    },
  }
}
</script>
