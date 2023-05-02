<template>
  <div>
    <v-layout v-if="fetchState.pending" justify-center class="centered">
      <v-progress-circular indeterminate size="50" />
    </v-layout>
    <div v-else-if="fetchState.error">
      <v-alert color="error">
        Failed to load page: {{ fetchState.error }}
      </v-alert>
    </div>

    <div v-show="!fetchState.pending && !fetchState.error">
      <slot />
    </div>
  </div>
</template>

<script>
export default {
  props: {
    fetchState: {
      type: Object,
      required: true
    }
  },
}
</script>

<style scoped>
.centered {
  margin-top: 50vh;
  transform: translateY(-50%);
}
</style>
