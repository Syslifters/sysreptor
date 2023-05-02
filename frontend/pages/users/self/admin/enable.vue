<template>
  <v-container>
    <v-alert v-if="errorMessage" color="error">
      {{ errorMessage }}
    </v-alert>
    <div v-else>
      <h1>Welcome, mighty Superuser</h1>
      <v-alert color="success">
        Your superuser permissions are now enabled. Use them responsibly.
      </v-alert>
      <s-btn to="/" nuxt color="primary">Continue</s-btn>
    </div>
  </v-container>
</template>

<script>
import { redirectToReAuth } from '~/utils/auth';

export default {
  async asyncData({ $axios, $auth, route }) {
    let errorMessage = null;
    try {
      const user = await $axios.$post('/pentestusers/self/admin/enable/', {});
      $auth.setUser(user);
    } catch (error) {
      if (error?.response?.data?.code === 'reauth-required') {
        redirectToReAuth({ auth: $auth, route });
      } else {
        errorMessage = error?.response?.detail || 'Failed to enable superuser permissions';
      }
    }
    return { errorMessage };
  },
}
</script>
