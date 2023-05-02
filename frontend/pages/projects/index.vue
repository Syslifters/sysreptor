<template>
  <div>
    <s-sub-menu>
      <v-tab :to="`/projects/`" nuxt exact>Active Projects</v-tab>
      <v-tab :to="`/projects/finished/`" nuxt>Finished Projects</v-tab>
      <v-tab v-if="archivingEnabled" to="/projects/archived/" nuxt>Archived Projects</v-tab>
    </s-sub-menu>

    <list-view url="/pentestprojects/?readonly=false">
      <template #title>Projects</template>
      <template #actions>
        <s-btn to="/projects/new/" nuxt color="primary" class="ml-1 mr-1">
          <v-icon>mdi-plus</v-icon>
          Create
        </s-btn>
        <btn-import :import="performImport" />
      </template>
      <template #item="{item}">
        <project-list-item :item="item" />
      </template>
    </list-view>
  </div>
</template>

<script>
import { uploadFileHelper } from '~/utils/upload';

export default {
  head: {
    title: 'Projects',
  },
  computed: {
    archivingEnabled() {
      return this.$store.getters['apisettings/settings'].features.archiving;
    },
  },
  methods: {
    async performImport(file) {
      const projects = await uploadFileHelper(this.$axios, '/pentestprojects/import/', file);
      this.$router.push({ path: `/projects/${projects[0].id}/` });
    },
  }
}
</script>
