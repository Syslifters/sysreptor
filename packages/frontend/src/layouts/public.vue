<template>
  <div class="height-fullscreen">
    <nuxt-loading-indicator :height="2" :color="false" />
    <v-app-bar absolute height="48" elevation="0" color="header" class="menu-appbar">
      <div class="menu-drawer-header border-0">
        <svg-logo-text />
        <span class="license-text">{{ licenseTextFull }}</span>
      </div>
      <v-spacer />
      <user-info-menu-item />
    </v-app-bar>

    <v-main class="main-container">
      <slot name="default" />
    </v-main>
  </div>
</template>

<script setup lang="ts">
const apiSettings = useApiSettings();

const licenseTextFull = computed(() => {
  const license = apiSettings.settings?.license?.type || 'community';
  return {
    community: '/Community Edition',
    professional: '/PRO',
  }[license] || '';
});   
</script>

<style lang="scss" scoped>
@use 'sass:map';
@use "@base/assets/vuetify.scss" as vuetify;

.height-fullscreen {
  height: 100vh;
}

.nuxt-loading-indicator {
  background: rgb(var(--v-theme-primary));
}

.main-container {
  height: 100%;
}

.menu-appbar {
  font-size: larger;
  z-index: 0 !important;
  margin-top: -1px;
  border-bottom-width: vuetify.$navigation-drawer-border-thin-width;
  border-bottom-style: vuetify.$navigation-drawer-border-style;
  border-bottom-color: vuetify.$navigation-drawer-border-color;
}
.v-app-bar-nav-icon:hover svg {
  fill: rgb(var(--v-theme-primary));
}

.menu-drawer-header {
  display: flex;
  flex-direction: row;
  align-items: center;
  flex-grow: 0;
  flex-shrink: 0;
  padding-left: 0.7rem;
  padding-right: 0.7rem;
}

.license-text {
  height: 28px;
  display: flex;
  flex-direction: column-reverse;
  font-weight: 900;
  font-size: 1.3rem;
  line-height: 1;
  color: rgb(var(--v-theme-logo));
}
</style>
