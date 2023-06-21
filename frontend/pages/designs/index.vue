<template>
  <div>
    <s-sub-menu v-if="privateDesignsEnabled">
      <v-tab :to="`/designs/`" nuxt exact>Global Designs</v-tab>
      <v-tab :to="`/designs/private/`" nuxt>Private Designs</v-tab>
    </s-sub-menu>

    <list-view url="/projecttypes/?scope=global&ordering=name">
      <template #title>Global Designs</template>
      <template #actions v-if="$auth.hasScope('designer')">
        <design-create-design-dialog project-type-scope="global" />
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
    title: 'Designs',
  },
  computed: {
    privateDesignsEnabled() {
      return this.$store.getters['apisettings/settings'].features.private_designs;
    },
  },
  methods: {
    async performImport(file) {
      const designs = await uploadFileHelper(this.$axios, '/projecttypes/import/', file, { scope: 'global' });
      this.$router.push({ path: `/designs/${designs[0].id}/` });
    },
  }
}
</script>
