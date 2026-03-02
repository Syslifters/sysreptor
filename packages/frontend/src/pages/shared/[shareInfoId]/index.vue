<template>
  <centered-view>
    <s-card v-if="error" class="w-100">
      <v-toolbar
        title="Invalid shared link"
        color="error"
        flat
      />
      <v-card-text>
        <p>Maybe the shared link expired or was revoked.</p>
      </v-card-text>
    </s-card>
    <s-card v-else-if="shareInfo?.password_required" class="w-100">
      <v-toolbar 
        title="Access Shared Data"
        color="header" 
        flat 
      />
      <v-form @submit.prevent="submitPasswordForm">
        <v-card-text>
          <s-password-field
            v-model="passwordForm.data.password"
            :error-messages="passwordForm.error"
            label="Password"
            required
            class="mt-4"
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
    <s-card v-else class="w-100">
      <div class="mt-4 d-flex flex-column align-center">
        <v-progress-circular indeterminate size="50" />
      </div>
    </s-card>
  </centered-view>
</template>

<script setup lang="ts">
definePageMeta({
  auth: false,
  layout: 'public',
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
  if (!shareInfo.value) {
    return;
  }
  try {
    passwordForm.value.inProgress = true;
    await $fetch(`/api/public/shareinfos/${shareInfo.value.id}/auth/`, {
      method: 'POST',
      body: passwordForm.value.data,
    });
    await shareInfoStore.fetchById(shareInfo.value.id);
    await navigateTo(`/shared/${shareInfo.value.id}/notes/`);
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
