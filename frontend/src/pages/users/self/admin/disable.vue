<template>
  <v-container>
    <h1>Goodbye, Superuser</h1>
    <v-alert color="success">
      You superuser permissions have been disabled. You are now a regular user again.
    </v-alert>
    <s-btn @click="auth.redirect(route.query.next)" color="primary" text="Continue" class="mt-4" />
  </v-container>
</template>

<script setup lang="ts">
const route = useRoute();
const auth = useAuth();
useLazyAsyncData(async () => {
  try {
    auth.store.user = await $fetch('/api/v1/pentestusers/self/admin/disable/', {
      method: 'POST',
      body: {}
    });
  } catch {
    // ignore
  }
});
</script>
