<template>
  <v-container fluid class="fill-height">
    <v-row justify="center">
      <v-col xs="12" sm="8" md="4" align-self="center">
        <login-form v-if="step === 'local'" :username="auth.user.value!.username" @login="auth.redirect()">
          <template #title>Re-Authenticate</template>
          <template #actions>
            <s-btn-other
              @click="cancelReAuth"
              text="Cancel"
            />
            <s-btn-secondary
              v-if="apiSettings.settings!.auth_providers.length > 1"
              @click="step = Step.LIST"
              text="Back"
            />
          </template>
        </login-form>
        <login-provider-form v-else ref="loginProviderForm" :reauth="true">
          <template #title>Re-Authenticate</template>
          <template #local>
            <v-list-item>
              <s-btn-secondary
                @click="step = Step.LOCAL"
                text="Login with local user"
                block
              />
            </v-list-item>
          </template>
          <template #actions>
            <s-btn-other
              v-if="apiSettings.settings!.auth_providers.length > 1"
              @click="cancelReAuth"
              text="Cancel"
            />
          </template>
        </login-provider-form>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { AuthProviderType } from "~/utils/types";

definePageMeta({
  title: 'Re-Authenticate',
});

const route = useRoute();
const router = useRouter();
const auth = useAuth();
const apiSettings = useApiSettings();

enum Step {
  LIST = 'list',
  LOCAL = 'local',
}

const step = ref(Step.LIST);

useLazyAsyncData(async () => {
  if (!route.query?.logout) {
    const authProviders = apiSettings.settings!.auth_providers;
    let defaultAuthProvider = authProviders.find(p => p.id === apiSettings.settings!.default_reauth_provider);
    if (!defaultAuthProvider && authProviders.length === 1) {
      defaultAuthProvider = authProviders[0];
    }
    if (!defaultAuthProvider && auth.user.value!.can_login_local) {
      defaultAuthProvider = authProviders.find(p => p.type === AuthProviderType.LOCAL);
    }
    if (defaultAuthProvider?.type === AuthProviderType.LOCAL) {
      step.value = Step.LOCAL;
    } else if (defaultAuthProvider) {
      await auth.authProviderLoginBegin(defaultAuthProvider, { reauth: true });
    }
  }
});

function cancelReAuth() {
  auth.store.clearAuthRedirect();
  router.back();
}
</script>
