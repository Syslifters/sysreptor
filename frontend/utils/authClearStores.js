export default function ({ $auth, store }) {
  $auth.$storage.watchState('loggedIn', () => {
    // Clear user specific data from Vuex store on logout and login
    // to prevent seeing cached data of other users in the UI.
    store.commit('projects/clear');
    store.commit('projecttypes/clear');
    store.commit('templates/clear');
    store.commit('usernotes/clear');
  });
}
