export const sate = () => ({
  languages: null,
});

export const mutations = {
  setLanguages(state, languages) {
    state.languages = languages;
  }
};

export const actions = {
  async getLanguages({ commit, state }) {
    if (state.languages) {
      return state.languages;
    }
    const languages = await this.$axios.$get('/utils/languages/');
    commit('setLanguages', languages);
    return languages;
  },
};
