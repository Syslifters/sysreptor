import { apiCachedStateFactory } from "~/utils/state";

const store = apiCachedStateFactory(id => '/projecttypes/' + (id ? (id + '/') : ''));

export const state = () => ({
  ...store.state(),
  predefinedFindingFields: null,
});
export const mutations = {
  ...store.mutations,
  setPredefinedFindingFields(state, data) {
    state.predefinedFindingFields = data;
  },
};

export const actions = {
  ...store.actions,
  async getPredefinedFindingFields({ state, commit }) {
    if (state.predefinedFindingFields !== null) {
      return state.predefinedFindingFields;
    }

    const data = await this.$axios.$get('/projecttypes/predefinedfields/findings/');
    commit('setPredefinedFindingFields', data);
    return data;
  }
};
