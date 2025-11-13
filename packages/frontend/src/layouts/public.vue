<template>
  <div class="height-fullscreen">
    <nuxt-loading-indicator :height="2" :color="false" />
    <v-app-bar absolute height="48" elevation="0" color="header" class="menu-appbar">
      <header-logo-text license-text-variant="long" class="border-0" />
      <v-spacer />
      <user-info-menu-item />
    </v-app-bar>

    <v-main class="main-container">
      <slot name="default" />
    </v-main>
  </div>
</template>

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
</style>
