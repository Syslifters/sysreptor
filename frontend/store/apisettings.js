export const sate = () => ({
  settings: null,
  getSettingsSync: null,
});

export const mutations = {
  setSettings(state, settings) {
    state.settings = settings;
  }
};

export const actions = {
  async fetchSettings({ commit }) {
    const settings = await this.$axios.$get('/utils/settings/');
    commit('setSettings', settings);
    return settings;
  },
  async getSettings({ dispatch, state }) {
    if (state.settings) {
      return state.settings;
    } else if (state.getSettingsSync) {
      return await state.getSettingsSync;
    } else {
      // Use only 1 fetch requests
      // Prevent performing the same requests multiple times when many components want to access data at the same time
      try {
        state.getSettingsSync = dispatch('fetchSettings');
        return await state.getSettingsSync;
      } finally {
        state.getSettingsSync = null;
      }
    }
  },
};

export const getters = {
  settings(state) {
    return state.settings;
  },
  is_professional_license(state) {
    return state.settings?.license?.type === 'professional';
  },
}
