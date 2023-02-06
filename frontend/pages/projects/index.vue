<template>
  <div>
    <s-sub-menu>
      <v-tab :to="`/projects/`" nuxt exact>Active Projects</v-tab>
      <v-tab :to="`/projects/finished/`" nuxt>Finished Projects</v-tab>
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
import { uploadFile } from '~/utils/upload';

export default {
  methods: {
    async performImport(file) {
      const projects = await uploadFile(this.$axios, '/pentestprojects/import/', file);
      this.$router.push({ path: `/projects/${projects[0].id}/project/` });
    },
  }
}
</script>
