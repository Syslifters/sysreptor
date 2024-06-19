<template>
  <s-card class="mt-4">
    <v-card-title>Multi Factor Authentication</v-card-title>
    <v-card-text>
      <p>
        If this user lost all its MFA methods and cannot log in anymore, you can remove all MFA devices to disable MFA.
      </p>

      <v-list>
        <v-list-item
          v-for="mfaMethod in mfaMethods"
          :key="mfaMethod.id"
          :prepend-icon="mfaMethodChoices.find(c => c.value === mfaMethod.method_type)!.icon"
        >
          <v-list-item-title>
            {{ mfaMethod.name }}
            <template v-if="mfaMethod.is_primary">
              <v-chip size="small" class="ml-3">Primary</v-chip>
            </template>
          </v-list-item-title>
          <template #append>
            <btn-delete button-variant="icon" :delete="() => deleteMfaMethod(mfaMethod)" :disabled="!canEdit" />
          </template>
        </v-list-item>
        <v-list-item
          v-if="mfaMethods.length === 0"
          title="Multi Factor Authentication is disabled"
        />
      </v-list>
    </v-card-text>
  </s-card>
</template>

<script setup lang="ts">
const route = useRoute();
const auth = useAuth();

const user = await useFetchE<User>(`/api/v1/pentestusers/${route.params.userId}/`, { method: 'GET' })
const mfaMethods = await useFetchE<MfaMethod[]>(`/api/v1/pentestusers/${route.params.userId}/mfa/`, { method: 'GET' });
const canEdit = computed(() => auth.permissions.value.user_manager && !user.value.is_system_user)

async function deleteMfaMethod(mfaMethod: MfaMethod) {
  await $fetch(`/api/v1/pentestusers/${route.params.userId}/mfa/${mfaMethod.id}/`, { method: 'DELETE' });
  mfaMethods.value = mfaMethods.value.filter(m => m.id !== mfaMethod.id);
}
</script>
