<template>
  <v-container>
    <div v-if="pending" class="mt-4 d-flex flex-column align-center">
      <v-progress-circular indeterminate size="50" />
    </div>
    <v-alert v-else-if="error" color="error" :text="error.message" />
    <div v-else>
      <h1>Welcome, mighty Superuser</h1>
      <v-alert color="success">
        Your superuser permissions are now enabled. Use them responsibly.
      </v-alert>
      <s-btn @click="auth.redirect(route.query.next)" color="primary" text="Continue" class="mt-4" />
    </div>
  </v-container>
</template>

<script setup lang="ts">
const route = useRoute();
const auth = useAuth();
const { error, pending } = useLazyAsyncData(async () => {
  try {
    auth.store.user = await $fetch<User>('/api/v1/pentestusers/self/admin/enable/', {
      method: 'POST',
      body: {}
    });
  } catch (error: any) {
    if (error?.data?.code === 'reauth-required') {
      await auth.redirectToReAuth();
    } else if (error?.data?.detail) {
      throw new Error(error.data.detail);
    } else {
      throw new Error('Failed to enable superuser permissions');
    }
  }
});
</script>
