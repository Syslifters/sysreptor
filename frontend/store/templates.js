import { apiCachedStateFactory } from "~/utils/state";

const store = apiCachedStateFactory(id => '/findingtemplates/' + (id ? (id + '/') : ''));

export const state = () => ({
  ...store.state(),
  fieldDefinition: null,
});

export const mutations = {
  ...store.mutations,
  setFieldDefinition(state, data) {
    state.fieldDefinition = data;
  },
};

export const actions = {
  ...store.actions,
  getFieldDefinition({ commit, state }) {
    if (state.fieldDefinition !== null) {
      return state.fieldDefinition;
    }
    const res = this.$axios.$get('/findingtemplates/fielddefinition/');
    commit('setFieldDefinition', res);
    return res;
  },
};
