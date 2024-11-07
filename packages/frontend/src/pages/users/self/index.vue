<template>
  <v-form ref="form">
    <edit-toolbar :data="user" :form="$refs.form as VForm" :save="performSave" />

    <user-info-form v-model="user" :errors="serverErrors" />
  </v-form>
</template>

<script setup lang="ts">
import { VForm } from 'vuetify/components';

const auth = useAuth();
const user = await useFetchE<User>('/api/v1/pentestusers/self/', { method: 'GET', deep: true });

const serverErrors = ref<any|null>(null);
async function performSave(data: User) {
  try {
    const user = await $fetch<User>('/api/v1/pentestusers/self/', {
      method: 'PATCH',
      body: data,
    });
    serverErrors.value = null;
    auth.store.user = user
  } catch (error: any) {
    if (error?.statusCode === 400 && error?.data) {
      serverErrors.value = error.data;
    }
    throw error;
  }
}
</script>
