import type { NavigateToOptions } from '#app/composables/router'
import type { LocationQueryValue } from "#vue-router";
import { AuthProviderType } from "@/utils/types";
import type { AuthProvider, User } from "@/utils/types";

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    authRedirect: null as string | null,
  }),
  getters: {
    permissions(state) {
      const apiSettings = useApiSettings();
      return {
        superuser: state.user?.is_superuser || false,
        admin: state.user?.scope.includes('admin') || false,
        user_manager: state.user?.scope.includes('user_manager') || false,
        designer: state.user?.scope.includes('designer') || false,
        template_editor: state.user?.scope.includes('template_editor') || false,
        private_designs: (state.user && apiSettings.settings?.features.private_designs) || false,
        create_projects: (state.user && (!state.user.is_guest || state.user.scope.includes('admin') || (state.user.is_guest && apiSettings.settings?.guest_permissions.create_projects))) || false,
        import_projects: (state.user && (!state.user.is_guest || state.user.scope.includes('admin') || (state.user.is_guest && apiSettings.settings?.guest_permissions.import_projects))) || false,
        delete_projects: (state.user && (!state.user.is_guest || state.user.scope.includes('admin') || (state.user.is_guest && apiSettings.settings?.guest_permissions.delete_projects))) || false,
        update_project_settings: (state.user && (!state.user.is_guest || state.user.scope.includes('admin') || (state.user.is_guest && apiSettings.settings?.guest_permissions.update_project_settings))) || false,
        edit_projects: (state.user && (!state.user.is_guest || state.user.scope.includes('admin') || (state.user.is_guest && apiSettings.settings?.guest_permissions.edit_projects))) || false,
        archive_projects: (apiSettings.settings?.features.archiving && state.user && (!state.user.is_guest || state.user.scope.includes('admin') || (state.user.is_guest && apiSettings.settings?.guest_permissions.update_project_settings))) || false,
        view_license: state.user?.is_superuser || state.user?.is_user_manager || state.user?.is_system_user || false,
        view_backup: (apiSettings.isProfessionalLicense && state.user?.scope.includes('admin')) || false,
      };
    },
  },
  actions: {
    setAuthRedirect(redirect?: LocationQueryValue|LocationQueryValue[]) {
      if (Array.isArray(redirect)) {
        redirect = redirect[0];
      }

      if (redirect && redirect.startsWith('/')) {
        this.authRedirect = redirect;
      }
    },
    clearAuthRedirect() {
      this.authRedirect = null;
    }
  },
  persist: {
    storage: persistedState.sessionStorage,
    paths: ['authRedirect'],
  }
})

export function useAuth() {
  const store = useAuthStore();
  const user = computed(() => store.user);
  const loggedIn = computed(() => !!store.user);

  async function fetchUser() {
    try {
      store.user = await $fetch<User>('/api/v1/pentestusers/self/', {
        method: 'GET',
      });
    } catch {
      store.user = null;
    }
    return store.user;
  }

  async function redirect(to?: LocationQueryValue|LocationQueryValue[]) {
    let redirect = store.authRedirect || '/';
    store.authRedirect = null;
    if (Array.isArray(to) && to[0]) {
      redirect = to[0];
    } else if (to && typeof to === 'string') {
      redirect = to;
    }
    if (!redirect.startsWith('/')) {
      redirect = '/';
    }

    const external = ['/api', '/ws', '/admin', '/static'].some(p => redirect.startsWith(p));
    return await navigateTo(redirect, { external });
  }

  async function redirectToReAuth(options?: NavigateToOptions) {
    const route = useRoute();
    store.setAuthRedirect(route.fullPath);
    return await navigateTo('/login/reauth/', options);
  }

  async function logout() {
    try {
      await $fetch('/api/v1/auth/logout/', {
        method: 'POST',
        body: {}, // Send request as JSON to prevent CSRF errors
      });
    } catch {
      // Ignore errors
    }
    await navigateTo('/login/');
    store.user = null;
  }

  async function authProviderLoginBegin(authProvider: AuthProvider, options = { reauth: false }) {
    if (authProvider.type === AuthProviderType.LOCAL) {
      await navigateTo('/login/local/');
    } else if (authProvider.type === AuthProviderType.REMOTEUSER) {
      try {
        await $fetch('/api/v1/auth/login/remoteuser/', {
          method: 'POST',
          body: {}
        });
        await fetchUser();
        await redirect();
      } catch (error) {
        requestErrorToast({ error, message: 'Login failed' });
      }
    } else if (authProvider.type === AuthProviderType.OIDC) {
      const url = new URL(`/api/v1/auth/login/oidc/${authProvider.id}/begin/`, window.location.href);
      if (options.reauth) {
        url.searchParams.append('reauth', 'true');
      }
      await navigateTo(url.href, { external: true });
    }
  }

  return {
    loggedIn,
    user,
    store,
    permissions: computed(() => store.permissions),
    logout,
    redirect,
    redirectToReAuth,
    fetchUser,
    authProviderLoginBegin,
  };
}
