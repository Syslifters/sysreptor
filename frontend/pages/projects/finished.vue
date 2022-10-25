<template>
  <div>
    <s-sub-menu>
      <v-tab :to="`/projects/`" exact>Active Projects</v-tab>
      <v-tab :to="`/projects/finished/`">Finished Projects</v-tab>
    </s-sub-menu>

    <list-view url="/pentestprojects/?readonly=true">
      <template #title>Finished Projects</template>
      <template #item="{item}">
        <project-list-item :item="item" />
      </template>
    </list-view>
  </div>
</template>
