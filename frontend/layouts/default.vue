<template>
  <v-app>
    <v-app-bar app absolute dense elevation="0">
      <v-tabs class="main-menu" hide-slider>
        <v-tab to="/" active-class="no-highlight" exact :ripple="false">
          <v-toolbar-title>SysReptor</v-toolbar-title>
        </v-tab>
        <template v-if="$auth.loggedIn">
          <v-tab to="/projects/" :ripple="false">Projects</v-tab>
          <v-tab to="/templates/" :ripple="false">Templates</v-tab>
          <v-tab to="/designer/" :ripple="false">Designer</v-tab>
          <v-tab v-if="$auth.hasScope('user_manager')" to="/users/" :ripple="false">Users</v-tab>
          <v-spacer />

          <user-info-menu-item />
        </template>
      </v-tabs>
    </v-app-bar>

    <v-main>
      <Nuxt />
    </v-main>
  </v-app>
</template>

<style lang="scss" scoped>
.main-menu :deep() {
  font-size: larger;

  .v-tabs-bar {
    background-color: $syslifters-darkblue !important;

    .v-tab {
      color: $syslifters-white !important;
      text-transform: inherit !important;
      font-size: 1rem;

      &:hover, &.v-tab--active:not(.no-highlight) {
        color: $syslifters-orange !important;
        &::before {
          opacity: 0 !important;
        }
      }
    }
  }
}
</style>
