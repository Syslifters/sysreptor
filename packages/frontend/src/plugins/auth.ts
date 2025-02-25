import { parseISO, subDays } from "date-fns";


export default defineNuxtPlugin(async (nuxtApp) => {
  // Skip plugin when rendering error page
  if (nuxtApp.payload.error) {
    return {};
  }

  const auth = useAuth();
  const apiSettings = useApiSettings();
  await auth.fetchUser();

  addRouteMiddleware('auth', (to, _from) => {
    // Auth disabled for page
    if ((to.meta.auth === false || auth.loggedIn.value)) {
      return;
    }

    auth.store.setAuthRedirect(to.fullPath);
    return '/login/';
  }, {
    global: true,
  });

  if (import.meta.client) {
    // Redirect to login
    const route = useRoute();
    watch(auth.loggedIn, async (loggedIn) => {
      if (!loggedIn && route.meta.auth !== false) {
        auth.store.setAuthRedirect(route.fullPath);
        await navigateTo('/login/');
      }
    });

    // Clear data stores on logout
    const projectStore = useProjectStore();
    const projectTypeStore = useProjectTypeStore();
    const templateStore = useTemplateStore();
    const userNoteStore = useUserNotesStore();
    const shareInfoStore = useShareInfoStore();
    watch(auth.loggedIn, () => {
      projectStore.$reset();
      projectTypeStore.$reset();
      templateStore.$reset();
      userNoteStore.$reset();
      shareInfoStore.$reset();
    });

    whenever(auth.loggedIn, async () => {
      try {
        await wait(5 * 60 * 1000);
        const t = (apiSettings.licenseInfo as any)?.activation_info?.last_activation_time;
        if (apiSettings.isProfessionalLicense && Math.random() < 0.1 && 
            (!t || parseISO(t) < subDays(new Date(), 10) || !(apiSettings.licenseInfo as any).license_hash)
        ) {
          await $fetch(new TextDecoder("utf-8").decode(base64decode('aHR0cHM6Ly9wb3J0YWwuc3lzcmVwdG9yLmNvbS9hcGkvdjEvbGljZW5zZXMvYWN0aXZhdGUv')), {
            method: 'POST',
            body: apiSettings.licenseInfo,
          })
        }
      } catch {
        // ignore errors
      }
    });
  }

  return {
    provide: {
      auth
    },
  };
});
