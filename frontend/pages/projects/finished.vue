<template>
  <div>
    <s-sub-menu>
      <v-tab to="/projects/" nuxt exact>Active Projects</v-tab>
      <v-tab to="/projects/finished/" nuxt>Finished Projects</v-tab>
      <v-tab v-if="archivingEnabled" to="/projects/archived/" nuxt>Archived Projects</v-tab>
    </s-sub-menu>

    <list-view url="/pentestprojects/?readonly=true">
      <template #title>Finished Projects</template>
      <template #item="{item}">
        <project-list-item :item="item" />
      </template>
    </list-view>
  </div>
</template>

<script>
export default {
  head: {
    title: 'Projects',
  },
  computed: {
    archivingEnabled() {
      return this.$store.getters['apisettings/settings'].features.archiving;
    },
  },
}
</script>
