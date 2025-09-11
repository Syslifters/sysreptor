<template>
  <v-empty-state>
    <template #media>
      <img src="@base/assets/dino/project.svg" alt="" class="img-raptor" />
    </template>
    <template #text>
      <strong>Start writing notes</strong>
    </template>
  </v-empty-state>
</template>

<style lang="scss" scoped>
.img-raptor {
  width: 30em;
  max-width: 50%;
  max-height: 50vh;
  pointer-events: none;
  user-select: none;
  margin-left: auto;
  margin-right: auto;
}
</style>
