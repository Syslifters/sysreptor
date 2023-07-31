import { sortBy } from "lodash";

export const state = () => ({
  fieldDefinition: null,
  fieldDefinitionSync: null,
});

export const mutations = {
  setFieldDefinition(state, data) {
    state.fieldDefinition = data;
  },
  setFieldDefinitionSync(state, data) {
    state.fieldDefinitionSync = data;
  }
};

export const actions = {
  async create(ctx, data) {
    return await this.$axios.$post('/findingtemplates/', data);
  },
  async update(ctx, obj) {
    return await this.$axios.$patch(`/findingtemplates/${obj.id}/`, obj);
  },
  async delete(ctx, obj) {
    return await this.$axios.$delete(`/findingtemplates/${obj.id}/`);
  },
  async createFromFinding(ctx, { template, projectId }) {
    return await this.$axios.$post(`/findingtemplates/fromfinding/`, { ...template, project: projectId });
  },
  async fetchFieldDefinition({ commit }) {
    const res = await this.$axios.$get('/findingtemplates/fielddefinition/');
    commit('setFieldDefinition', res);
    return res;
  },
  async getFieldDefinition({ state, commit, dispatch }) {
    if (state.fieldDefinition !== null) {
      return state.fieldDefinition;
    } else if (state.fieldDefinitionSync) {
      return await state.fieldDefinitionSync;
    }

    try {
      const fetchFieldDefinition = dispatch('fetchFieldDefinition');
      commit('setFieldDefinitionSync', fetchFieldDefinition);
      return await fetchFieldDefinition;
    } finally {
      commit('setFieldDefinitionSync', null);
    }
  },
};

export const getters = {
  fieldDefinitionList(state, _geters, _rootState, rootGetters) {
    if (!state.fieldDefinition) {
      return [];
    }

    const fieldFilterHiddenFields = rootGetters['settings/templateFieldFilterHiddenFields'];
    return sortBy(
      Object.keys(state.fieldDefinition).map(id => ({ id, visible: !fieldFilterHiddenFields.includes(id), ...state.fieldDefinition[id] })),
      [(d) => {
        const originOrder = { core: 1, predefined: 2, custom: 3 };
        return originOrder[d.origin] || 10;
      }]);
  }
};
