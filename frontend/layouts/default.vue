<template>
  <v-app>
    <v-app-bar app absolute dense elevation="0">
      <v-tabs class="main-menu" hide-slider>
        <v-tab to="/" nuxt active-class="no-highlight" exact :ripple="false">
          <v-img src="/static/logo.svg" contain height="38" width="50" />
          SysReptor
          <v-badge content="Beta" color="primary" class="badge-beta" inline />
        </v-tab>
        <template v-if="$auth.loggedIn">
          <v-tab to="/projects/" nuxt :ripple="false">Projects</v-tab>
          <v-tab to="/templates/" nuxt :ripple="false">Templates</v-tab>
          <v-tab to="/designs/" nuxt :ripple="false">Designs</v-tab>
          <v-tab v-if="$auth.hasScope('user_manager')" to="/users/" nuxt :ripple="false">Users</v-tab>
          <v-tab to="/notes/personal/" nuxt :ripple="false">Notes</v-tab>
        </template>

        <v-spacer />
        <s-tooltip v-if="$auth.loggedIn && $auth.user.is_superuser && !$auth.hasScope('admin') && $store.getters['apisettings/is_professional_license']" bottom>
          <template #activator="{ on, attrs }">
            <s-btn to="/users/self/admin/enable/" v-bind="attrs" v-on="on" large dark class="btn-sudo">
              <v-icon>mdi-account-arrow-up</v-icon>
              Sudo
            </s-btn>
          </template>
          <span>Enable Superuser Permissions</span>
        </s-tooltip>
        <notification-menu-item v-if="$auth.loggedIn" />
        <s-tooltip bottom>
          <template #activator="{ on, attrs }">
            <s-btn icon dark href="https://docs.sysreptor.com/" target="_blank" v-bind="attrs" v-on="on">
              <v-icon>mdi-help-circle-outline</v-icon>
            </s-btn>
          </template>
          <span>Documentation</span>
        </s-tooltip>
        <user-info-menu-item v-if="$auth.loggedIn" />
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

.btn-sudo {
  height: 48px !important;
  background-color: inherit !important;
}
</style>
