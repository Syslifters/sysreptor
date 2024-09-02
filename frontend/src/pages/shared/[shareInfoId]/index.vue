<template>
  <v-container fluid class="fill-height">
    <v-row justify="center">
      <v-col xs="12" sm="8" md="4" align-self="center">
        <s-card v-if="error">
          <v-toolbar
            title="Invalid shared link"
            color="error"
            flat
          />
          <v-card-text>
            <p>Maybe the shared link expired or was revoked.</p>
          </v-card-text>
        </s-card>
        <s-card v-else-if="shareInfo?.password_required">
          <v-toolbar 
            title=""
            color="header" 
            flat 
          />
          <v-form @submit="submitPasswordForm">
            <v-card-text>
              <s-password-field
                v-model="passwordForm.data.password"
                :error-messages="passwordForm.error"
                label="Password"
                required
              />
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <s-btn-primary
                type="submit"
                text="Submit"
                :loading="passwordForm.inProgress"
              />
            </v-card-actions>
          </v-form>
        </s-card>
        <s-card v-else>
          <div class="mt-4 d-flex flex-column align-center">
            <v-progress-circular indeterminate size="50" />
          </div>
        </s-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
definePageMeta({
  auth: false,
  title: 'Shared',
})

const route = useRoute();
const shareInfoStore = useShareInfoStore();

const { data: shareInfo, error } = await useAsyncData(async () => {
  const shareInfo = await shareInfoStore.fetchById(route.params.shareInfoId as string);
  if (!shareInfo.password_required || shareInfo.password_verified) {
    await navigateTo(`/shared/${shareInfo.id}/notes/`);
    return null;
  }
  return shareInfo;
});

const passwordForm = ref({
  data: {
    password: '',
  },
  error: null as string|null,
  inProgress: false,
});
async function submitPasswordForm() {
  try {
    passwordForm.value.inProgress = true;
    await $fetch(`/api/v1/shareinfos/${shareInfo.value!.id}/auth/`, {
      method: 'POST',
      body: passwordForm.value.data,
    });
    await shareInfoStore.fetchById(shareInfo.value!.id);
    await navigateTo(`/shared/${shareInfo.value!.id}/notes/`);
  } catch (error: any) {
    if (error?.data?.detail) {
      passwordForm.value.error = error.data.detail;
    } else if (error?.data?.password) {
      passwordForm.value.error = error.data.password;
    } else {
      requestErrorToast({ error });
    }
  } finally {
    passwordForm.value.inProgress = false;
  }
}
</script>
