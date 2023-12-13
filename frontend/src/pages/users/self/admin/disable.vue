<template>
  <v-container>
    <div class="mt-4 d-flex flex-column align-center">
      <v-progress-circular indeterminate size="50" />
    </div>
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
    successToast('Superuser permissions disabled');
  } catch (error) {
    requestErrorToast({ message: 'Failed to disable superuser permissions', error });
  } finally {
    auth.redirect(route.query.next);
  }
});
</script>
