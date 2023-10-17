<template>
  <v-app class="height-fullscreen">
    <nuxt-loading-indicator :height="2" color="white" />
    <v-app-bar absolute density="compact" elevation="0" class="main-menu">
      <v-tabs hide-slider selected-class="main-menu-selected">
        <v-tab to="/" exact :ripple="false" class="no-highlight">
          <v-img src="/static/logo.svg" height="38" width="50" />
          SysReptor
          <v-badge :content="badgeText" color="primary" class="badge-pill" inline />
        </v-tab>
        <template v-if="auth.loggedIn.value">
          <v-tab to="/projects/" :ripple="false" text="Projects" />
          <v-tab to="/templates/" :ripple="false" text="Templates" />
          <v-tab to="/designs/" :ripple="false" text="Designs" />
          <v-tab v-if="auth.hasScope('user_manager')" to="/users/" :ripple="false" text="Users" />
          <v-tab to="/notes/personal/" :ripple="false" text="Notes" />
        </template>
      </v-tabs>

      <v-spacer />
      <s-tooltip text="Enable Superuser Permissions" location="bottom">
        <template #activator="{ props }">
          <s-btn
            v-if="auth.loggedIn.value && auth.user.value!.is_superuser && !auth.hasScope('admin') && apiSettings.isProfessionalLicense"
            :to="{path: '/users/self/admin/enable/', query: { next: route.fullPath }}"
            text="Sudo"
            prepend-icon="mdi-account-arrow-up"
            size="large"
            theme="dark"
            class="btn-sudo"
            v-bind="props"
          />
        </template>
      </s-tooltip>

      <notification-menu-item v-if="auth.loggedIn.value" />

      <s-tooltip text="Documentation" location="bottom">
        <template #activator="{ props }">
          <s-btn
            href="https://docs.sysreptor.com/" target="_blank"
            icon="mdi-help-circle-outline"
            theme="dark"
            class="bg-inherit"
            v-bind="props"
          />
        </template>
      </s-tooltip>

      <user-info-menu-item v-if="auth.loggedIn.value" />
    </v-app-bar>

    <v-main class="main-container">
      <slot />
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import capitalize from 'lodash/capitalize';

const auth = useAuth();
const apiSettings = useApiSettings();
const route = useRoute();

const badgeText = computed(() => {
  const license = apiSettings.settings?.license?.type || 'community';
  return capitalize(license);
});
</script>

<style lang="scss" scoped>
@use "@/assets/settings.scss" as settings;

.height-fullscreen {
  height: 100vh;
}

.main-container {
  height: 100%;

  & > :deep(.v-main__wrap) {
    height: 100%;
    overflow-y: auto;
  }
}

.badge-pill {
  margin-bottom: 0.7em;

  &:deep(.v-badge__wrapper) {
    margin-left: 0;
  }
}

.main-menu :deep() {
  font-size: larger;
  background-color: settings.$sysreptor-darkblue !important;
  z-index: 0 !important;

  .v-tab {
    color: settings.$sysreptor-white !important;
    text-transform: inherit !important;
    font-size: 1rem;

    &:hover , &.main-menu-selected:not(.no-highlight) {
      color: settings.$sysreptor-orange !important;
      &::before {
        opacity: 0 !important;
      }
    }
  }
}

.btn-sudo {
  height: 48px !important;
  background-color: inherit !important;
}
</style>
