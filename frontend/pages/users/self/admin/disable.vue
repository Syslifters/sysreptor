<template>
  <v-container>
    <h1>Goodbye, Admin</h1>
    <v-alert color="success">
      You admin permissions have been disabled. You are now a regular user again.
    </v-alert>
    <s-btn to="/" nuxt color="primary">Continue</s-btn>
  </v-container>
</template>

<script>
export default {
  async asyncData({ $axios, $auth }) {
    try {
      const user = await $axios.$post('/pentestusers/self/admin/disable/');
      $auth.setUser(user);
    } catch (error) {
      
    }
  }
}
</script>
