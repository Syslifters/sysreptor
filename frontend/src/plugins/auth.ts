export default defineNuxtPlugin(async (nuxtApp) => {
  // Skip plugin when rendering error page
  if (nuxtApp.payload.error) {
    return {};
  }

  const auth = useAuth();
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
    watch(auth.loggedIn, () => {
      projectStore.clear();
      projectTypeStore.clear();
      templateStore.clear();
      userNoteStore.clear();
    });
  }

  return {
    provide: {
      auth
    },
  };
});
