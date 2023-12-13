<template>
  <v-container fluid>
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
    auth.store.user = await $fetch<User>('/api/v1/pentestusers/self/admin/enable/', {
      method: 'POST',
      body: {}
    });
    successToast('Superuser permissions enabled');
    auth.redirect(route.query.next);
  } catch (error: any) {
    if (error?.data?.code === 'reauth-required') {
      await auth.redirectToReAuth({ replace: true });
    } else {
      requestErrorToast({ message: 'Failed to enable superuser permissions', error });
      auth.redirect(route.query.next);
    }
  }
});
</script>
