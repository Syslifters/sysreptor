<template>
  <v-empty-state
    v-bind="$attrs"
    text-width="100%"
    size="48"
    class="s-sidebar-empty-state"
  >
  <template v-for="(_, name) in $slots" #[name]="slotData: any"><slot :name="name" v-bind="slotData" /></template>
  </v-empty-state>
</template>

<style lang="scss" scoped>
.s-sidebar-empty-state {
  height: 100%;
  max-width: 100%;
  padding-inline: 0.25rem;

  :deep(.v-empty-state__title),
  :deep(.v-empty-state__text) {
    max-width: 100%;
    text-wrap: balance;
  }
  :deep(.v-empty-state__title) {
    font-size: 1rem;
    line-height: 1.35;
    padding-inline: 0.25rem;
  }
  :deep(.v-empty-state__text) {
    font-size: 0.8125rem;
    line-height: 1.4;
    padding-inline: 0.25rem;
  }
  :deep(.v-empty-state__actions) {
    margin-top: 0.5rem;
  }
  :deep(.v-empty-state__action-btn.v-btn) {
    text-transform: none;
  }
}
</style>
