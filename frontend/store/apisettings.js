export const sate = () => ({
  languages: null,
  getLanguagesSync: null,
});

export const mutations = {
  setLanguages(state, languages) {
    state.languages = languages;
  }
};

export const actions = {
  async fetchLanguages({ commit }) {
    const languages = await this.$axios.$get('/utils/languages/');
    commit('setLanguages', languages);
    return languages;
  },
  async getLanguages({ dispatch, state }) {
    if (state.languages) {
      return state.languages;
    } else if (state.getLanguagesSync) {
      return await state.getLanguagesSync;
    } else {
      // Use only 1 fetch requests
      // Prevent performing the same requests multiple times when many components want to access data at the same time
      try {
        state.getLanguagesSync = dispatch('fetchLanguages');
        return await state.getLanguagesSync;
      } finally {
        state.getLanguagesSync = null;
      }
    }
  },
};
