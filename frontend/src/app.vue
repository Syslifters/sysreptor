<template>
  <nuxt-layout>
    <nuxt-page />
  </nuxt-layout>
</template>

<script setup lang="ts">
const route = useRoute();
useHead({
  titleTemplate: title => rootTitleTemplate(title, route),
})
</script>
