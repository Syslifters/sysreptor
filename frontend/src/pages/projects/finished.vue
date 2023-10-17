<template>
  <full-height-page>
    <template #header>
      <s-sub-menu class="flex-grow-0">
        <v-tab to="/projects/" exact text="Active Projects" />
        <v-tab to="/projects/finished/" text="Finished Projects" />
        <v-tab v-if="apiSettings.settings!.features.archiving" to="/projects/archived/" text="Archived Projects" />
      </s-sub-menu>
    </template>

    <list-view url="/api/v1/pentestprojects/?readonly=true">
      <template #title>Finished Projects</template>
      <template #item="{item}">
        <project-list-item :item="item" />
      </template>
    </list-view>
  </full-height-page>
</template>

<script setup lang="ts">
definePageMeta({
  title: 'Projects',
});

const apiSettings = useApiSettings();
</script>
