import { defineStore } from 'pinia';
import type { NavigateToOptions } from '#app/composables/router'
import type { LocationQueryValue } from "#vue-router";
import { AuthProviderType, type AuthProvider, type User, useApiSettings, type LoginResponse, LoginResponseStatus, UserPermission } from "#imports";

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    authRedirect: null as string | null,
  }),
  getters: {
    permissions(state) {
      const apiSettings = useApiSettings();
      const admin = state.user?.is_admin || false;
      return {
        superuser: state.user?.is_superuser || false,
        admin,
        private_designs: (state.user && !state.user.is_system_user && apiSettings.settings?.features.private_designs) || false,
        view_backup: (apiSettings.isProfessionalLicense && admin) || false,
      };
    },
    hasPermission(state) {
      return (permission: UserPermission|string) => {
        const apiSettings = useApiSettings();
        if (!state.user?.effective_permissions?.includes(permission)) {
          return false;
        }
        if (permission === UserPermission.PROJECT_SHARE_NOTES && !apiSettings.settings?.features.sharing) {
          return false;
        } else if ([UserPermission.PROJECT_ARCHIVE, UserPermission.PROJECT_RESTORE].includes(permission as UserPermission) && !apiSettings.settings?.features.archiving) {
          return false;
        }
        return true;
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
    storage: sessionStorage,
    pick: ['authRedirect'],
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

  async function redirectToReAuth(options?: NavigateToOptions & { authRedirect?: LocationQueryValue }) {
    const route = useRoute();
    store.setAuthRedirect(options?.authRedirect ?? route.fullPath);
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
    await navigateTo('/login/?logout=true');
    store.user = null;
  }

  async function finishLogin(response: LoginResponse) {
    if (response.status !== LoginResponseStatus.SUCCESS) {
      throw new Error('Login failed');
    }
    // Refresh settings to include authenticated settings
    const apiSettings = useApiSettings();
    await apiSettings.fetchSettings();

    apiSettings.licenseInfo = response.license!;

    return await fetchUser();
  }

  async function authProviderLoginBegin(authProvider: AuthProvider, options = { reauth: false }) {
    if (authProvider.type === AuthProviderType.LOCAL) {
      await navigateTo('/login/local/');
    } else if (authProvider.type === AuthProviderType.REMOTEUSER) {
      try {
        const res = await $fetch<LoginResponse>('/api/v1/auth/login/remoteuser/', {
          method: 'POST',
          body: {}
        });
        await finishLogin(res);
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
    hasPermission: (permission: UserPermission|string) => store.hasPermission(permission),
    logout,
    redirect,
    redirectToReAuth,
    fetchUser,
    authProviderLoginBegin,
    finishLogin,
  };
}
