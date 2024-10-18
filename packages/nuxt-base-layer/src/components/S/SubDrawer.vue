<template>
  <v-navigation-drawer
    :rail="!isExpanded"
    rail-width="36"
    width="180"
    permanent
    touchless
    color="drawer"
    class="subdrawer"
  >
    <v-list class="pa-0 h-100 d-flex flex-column" density="compact">
      <slot :is-expanded="isExpanded" />
      <v-spacer />
      <v-list-item 
        @click="localSettings.subDrawerExpanded = !localSettings.subDrawerExpanded"
        class="pa-0 ma-0"
        title="Collapse"
        :prepend-icon="isExpanded ? 'mdi-chevron-left' : 'mdi-chevron-right'" 
      />
    </v-list>
  </v-navigation-drawer>
</template>

<script setup lang="ts">
const localSettings = useLocalSettings();
const isExpanded = computed(() => localSettings.subDrawerExpanded);
</script>

<style lang="scss">
.subdrawer {
  scrollbar-width: none;
  &::-webkit-scrollbar { display: none; }

  .v-list-item {
    padding-inline: 6px !important;
    padding-top: 1em;
    padding-bottom: 1em;
  }
  .v-list-item__spacer {
    width: 1em !important;
  }

  .v-list-item--active {
    .v-list-item-title {
      font-weight: bold;
    }
  }
  .v-list-item--active, .v-list-item:hover {
    .v-list-item__prepend .v-icon, .v-list-item-title {
      color: rgb(var(--v-theme-primary));
    }
  }
}
</style>
