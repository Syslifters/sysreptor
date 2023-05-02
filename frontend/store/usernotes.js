import { groupBy, sortBy } from "lodash";
import { apiCachedStateFactory } from "~/utils/state";

const store = apiCachedStateFactory(id => '/pentestusers/self/notes/' + (id ? (id + '/') : ''));

export const state = () => ({
  ...store.state(),
  listAvailalbe: false,
});

export const mutations = {
  ...store.mutations,
  setAll(state, objs) {
    // Update/add findings
    for (const obj of objs) {
      this.commit('usernotes/set', obj);
    }
    // Remove deleted findings
    for (const obj of Object.values(state.data).filter(o => !objs.map(o2 => o2.id).includes(o.id))) {
      this.commit('usernotes/remove', obj);
    }
    state.listAvailalbe = true;
  }
};

export const actions = {
  ...store.actions,
  async fetchAll({ commit }) {
    const objs = await this.$axios.$get('/pentestusers/self/notes/');
    commit('setAll', objs);
    return objs;
  },
  async getAll({ dispatch, state }) {
    if (state.listAvailalbe) {
      return Object.values(state.data);
    }
    return await dispatch('fetchAll');
  },
  async sort({ commit, getters }, { noteGroups }) {
    sortNotes(noteGroups, note => commit('set', note));
    await this.$axios.$post('/pentestusers/self/notes/sort/', getters.notes);
  },
};

export const getters = {
  notes: (state) => {
    return Object.values(state.data);
  },
  noteGroups: (state) => {
    return groupNotes(state.data || []);
  },
}

export function groupNotes(noteList) {
  const groups = groupBy(noteList, 'parent');
    
  function collectChildren(parentId) {
    return sortBy(groups[parentId] || [], 'order')
      .map(note => ({ note, children: collectChildren(note.id) }));
  }
  return collectChildren(null);
}

export function sortNotes(noteGroups, commitNote) {
  function setParentAndOrder(children, parentId) {
    for (let i = 0; i < children.length; i++) {
      const note = {
        ...children[i].note,
        parent: parentId,
        order: i + 1
      };
      commitNote(note);
      setParentAndOrder(children[i].children, note.id);
    }
  }
  setParentAndOrder(noteGroups, null);
}
