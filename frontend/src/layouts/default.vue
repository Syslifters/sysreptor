<template>
  <div class="height-fullscreen">
    <nuxt-loading-indicator :height="2" :color="false" />
    <v-app-bar absolute height="48" elevation="0" color="header" class="menu-appbar">
      <v-app-bar-nav-icon v-if="auth.loggedIn.value" @click="navigationDrawerVisible = !navigationDrawerVisible" :ripple="false">
        <svg-logo />
      </v-app-bar-nav-icon>
      <div v-else class="menu-drawer-header border-0">
        <svg-logo-text />
        <span class="license-text">{{ licenseText }}</span>
      </div>
      
      <v-spacer />
      <v-breadcrumbs v-if="breadcrumbs" :items="breadcrumbs as any" class="font-weight-medium">
        <template #item="{ item, index }">
          <v-breadcrumbs-item :to="(item as Breadcrumb).to" v-on="(index === breadcrumbs!.length - 1) ? { 'click.prevent': () => {} } : {}">
            <v-icon v-if="(item as Breadcrumb).icon" :icon="(item as Breadcrumb).icon" />
            {{ (item as Breadcrumb).title }}
          </v-breadcrumbs-item>
        </template>
      </v-breadcrumbs>
      <v-spacer />

      <s-btn-icon
        v-if="auth.loggedIn.value"
        to="/notes/personal/"
        :active="false"
      >
        <v-icon icon="mdi-notebook" />
        <s-tooltip activator="parent" location="bottom" text="Personal Notes" />
      </s-btn-icon>
      <notification-menu-item v-if="auth.loggedIn.value" />
      <s-btn-icon href="https://docs.sysreptor.com/" target="_blank">
        <v-icon icon="mdi-help-circle" />
        <s-tooltip activator="parent" location="bottom" text="Documentation" />
      </s-btn-icon>
      <user-info-menu-item v-if="auth.loggedIn.value" />
    </v-app-bar>

    <v-navigation-drawer v-if="auth.loggedIn.value" v-bind="naviagtionDrawerProps" color="drawer" class="menu-drawer">
      <div class="menu-drawer-header" @click="navigationDrawerVisible = !navigationDrawerVisible">
        <svg-logo-text />
        <span class="license-text">{{ licenseText }}</span>
      </div>
      <v-list class="pt-0 menu-drawer-body">
        <v-list-item to="/projects/" title="Projects" prepend-icon="mdi-file-document" :active="route.path.startsWith('/projects')" />
        <v-list-item to="/templates/" title="Templates" prepend-icon="mdi-view-compact" :active="route.path.startsWith('/templates')" />
        <v-list-item to="/designs/" title="Designs" prepend-icon="mdi-pencil-ruler" :active="route.path.startsWith('/designs')" />
        <v-list-item to="/notes/personal/" title="Notes" prepend-icon="mdi-notebook" :active="route.path.startsWith('/notes')" />
        
        <template v-if="auth.permissions.value.superuser || auth.permissions.value.user_manager || auth.permissions.value.view_license">
          <v-list-item class="mt-6 pa-0" min-height="0">
            <v-list-subheader title="Administration" />
            <template #append>
              <template v-if="apiSettings.isProfessionalLicense">
                <s-btn-icon
                  v-if="auth.permissions.value.admin"
                  :to="{path: '/users/self/admin/disable/', query: { next: route.fullPath }}"
                  density="comfortable"
                >
                  <v-icon size="small" color="primary" icon="mdi-account-arrow-down" />
                  <s-tooltip activator="parent" text="Disable Superuser Permissions" />
                </s-btn-icon>
                <s-btn-icon
                  v-else
                  :to="{path: '/users/self/admin/enable/', query: { next: route.fullPath }}"
                  :disabled="!auth.user.value!.is_superuser" 
                  density="comfortable" 
                >
                  <v-icon size="small" icon="mdi-account-arrow-up" />
                  <s-tooltip activator="parent" text="Enable Superuser Permissions" />
                </s-btn-icon>
              </template>
            </template>
          </v-list-item>

          <v-list-item 
            to="/users/" 
            title="Users" 
            prepend-icon="mdi-account-multiple" 
            :active="route.path.startsWith('/users') && !route.path.startsWith('/users/self')"
            :disabled="!auth.permissions.value.user_manager" 
          />
          <v-list-item
            to="/backups/"
            prepend-icon="mdi-tools"
            :disabled="!auth.permissions.value.view_backup"
          >
            <template #title><pro-info>Backups</pro-info></template>
          </v-list-item>
          <license-info-menu-item />
        </template>
      </v-list>
    </v-navigation-drawer>

    <v-main class="main-container">
      <slot name="default" />
    </v-main>
  </div>
</template>

<script setup lang="ts">
const auth = useAuth();
const apiSettings = useApiSettings();
const route = useRoute();
const display = useDisplay();

const navigationDrawerVisible = ref(false);
const naviagtionDrawerProps = computed(() => ({
  absolute: true,
  ...(route.meta.toplevel && display.mdAndUp.value ? { 
    permanent: true,
  } : { 
    temporary: true,
    modelValue: navigationDrawerVisible.value,
    'onUpdate:modelValue': (value: boolean) => { navigationDrawerVisible.value = value },
  })
}));

const licenseText = computed(() => {
  const license = apiSettings.settings?.license?.type || 'community';
  return {
    community: '/CE',
    professional: '/PRO',
  }[license] || '';
});

// Breadcrumbs
const breadcrumbs = ref<Breadcrumbs>();
const nuxtApp = useNuxtApp();
const head = nuxtApp.vueApp._context.provides.usehead
function syncBreadcrumbs() {
  const bc = head.headEntries()
    .filter((e: any) => e.input?.breadcrumbs)
    .reverse()
    .map((e: any) => e.input.breadcrumbs.map((b: Breadcrumb) => ({ ...b, title: b.title || '...', disabled: false })))[0];
  if (bc) {
    breadcrumbs.value = [
      { icon: 'mdi-home', to: '/' },
      ...bc,
    ];
  } else {
    breadcrumbs.value = undefined;
  }
}
head.hooks.hook('dom:beforeRender', syncBreadcrumbs);
</script>

<style lang="scss" scoped>
@use 'sass:map';
@use "@/assets/vuetify.scss" as vuetify;

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

.v-breadcrumbs-item {
  .v-icon {
    font-size: 1.5em;
  }
}

.menu-drawer:deep() {
  .v-list-item__spacer {
    width: 1em;
  }
  .v-list-item--active {
    border-left: 0.5em solid rgb(var(--v-theme-primary));
    padding-left: calc(16px - 0.5em);

    .v-list-item__overlay {
      opacity: 0;
    }
    .v-list-item-title {
      font-weight: bold;
    }
  }
  .v-list-item:hover {
    .v-list-item__overlay {
      opacity: calc(#{map.get(vuetify.$states, 'hover')} * var(--v-theme-overlay-multiplier));
    }
  }
  .v-list-item--active, .v-list-item:hover {
    .v-list-item__prepend .v-icon, .v-list-item-title {
      color: rgb(var(--v-theme-primary));
    }
  }
}

.menu-drawer {
  height: 100% !important;
  top: 0 !important;
  border-right-width: 0;

  &-header {
    height: 48px;
    background-color: rgb(var(--v-theme-header));
    color: rgb(var(--v-theme-on-header));
    display: flex;
    flex-direction: row;
    align-items: center;
    flex-grow: 0;
    flex-shrink: 0;
    padding-left: 0.75rem;
    padding-right: 0.75rem;
    cursor: pointer;
    border-bottom-width: vuetify.$navigation-drawer-border-thin-width;
    border-bottom-style: vuetify.$navigation-drawer-border-style;
    border-bottom-color: vuetify.$navigation-drawer-border-color;
  }

  &-body {
    border-right-width: vuetify.$navigation-drawer-border-thin-width;
    border-right-style: vuetify.$navigation-drawer-border-style;
    border-right-color: vuetify.$navigation-drawer-border-color;
    flex-grow: 1;
    min-height: 0;
    overflow-y: auto !important;
  }

  &:deep(.v-navigation-drawer__content) {
    height: 100%;
    display: flex;
    flex-direction: column;
  }
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
