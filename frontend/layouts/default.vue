<template>
  <v-app>
    <v-app-bar app absolute dense elevation="0">
      <v-tabs class="main-menu" hide-slider>
        <v-tab to="/" active-class="no-highlight" exact :ripple="false">
          <v-img src="/logo.svg" contain height="38" width="50" />
          SysReptor
          <v-badge content="Beta" color="primary" class="badge-beta" inline />
        </v-tab>
        <template v-if="$auth.loggedIn">
          <v-tab to="/projects/" :ripple="false">Projects</v-tab>
          <v-tab to="/templates/" :ripple="false">Templates</v-tab>
          <v-tab to="/designer/" :ripple="false">Designer</v-tab>
          <v-tab v-if="$auth.hasScope('user_manager')" to="/users/" :ripple="false">Users</v-tab>
        </template>

        <v-spacer />
        <s-btn icon dark href="https://docs.sysreptor.com/" target="_blank">
          <v-icon>mdi-help-circle-outline</v-icon>
        </s-btn>
        <template v-if="$auth.loggedIn">
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
.badge-beta {
  margin-bottom: 0.7em;
  
  &:deep(.v-badge__wrapper) {
    margin-left: 0;
  }
}

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
