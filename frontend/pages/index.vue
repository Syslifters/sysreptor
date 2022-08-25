<template>
  <v-container>
    <h1>Pentest Report Creator</h1>
  </v-container>
</template>

<script>
export default {
  name: 'IndexPage',
  fetch() {
    this.$router.push('/projects/');
  }
}
</script>
