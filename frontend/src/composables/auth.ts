import { LocationQueryValue } from "#vue-router";
import { AuthProvider, AuthProviderType, User } from "@/utils/types";

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    authRedirect: null as string | null,
  }),
  actions: {
    setAuthRedirect(redirect?: LocationQueryValue|LocationQueryValue[]) {
      if (Array.isArray(redirect)) {
        redirect = redirect[0];
      }

      if (redirect && redirect.startsWith('/')) {
        this.authRedirect = redirect;
      }
    },
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
    const { data } = await useFetch<User>('/api/v1/pentestusers/self/', {
      method: 'GET',
    });
    store.user = data.value;
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

    const external = ['/api', '/admin', '/static'].some(p => redirect.startsWith(p));
    return await navigateTo(redirect, { external });
  }

  async function redirectToReAuth() {
    const route = useRoute();
    store.setAuthRedirect(route.fullPath);
    return await navigateTo('/login/reauth/');
  }

  async function logout() {
    await useFetch('/api/v1/auth/logout/', {
      method: 'POST',
      body: {}, // Send request as JSON to prevent CSRF errors
    });
    await navigateTo('/login/');
    store.user = null;
  }

  function hasScope(scope: string) {
    if (!user.value) {
      return false;
    }
    return user.value.scope.includes(scope);
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
    logout,
    redirect,
    redirectToReAuth,
    fetchUser,
    hasScope,
    authProviderLoginBegin,
  };
}
