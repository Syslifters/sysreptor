import { set as vueSet, del as vueDel } from "vue";
import { isObject, pick } from "lodash";

export function apiCachedStateFactory(buildUrl) {
  return {
    state: () => ({
      data: {},
    }),
    mutations: {
      set(state, obj) {
        if (obj.id in state.data) {
          Object.assign(state.data[obj.id], obj);
        } else {
          vueSet(state.data, obj.id, obj);
        }
      },
      update(state, obj) {
        if (!(obj.id in state.data) || !state.data[obj.id]) {
          return;
        }
    
        updateObjectReactive(state.data[obj.id], obj);
      },
      remove(state, obj) {
        if (obj.id in state.data) {
          vueDel(state.data, obj.id);
        }
      }
    },
    actions: {
      async fetchById({ commit }, id) {
        const obj = await this.$axios.$get(buildUrl(id));
        commit('set', obj);
        return obj;
      },
      async getById({ dispatch, state }, id) {
        if (id in state.data) {
          return state.data[id];
        }
        return await dispatch('fetchById', id);
      },
      async create({ commit }, data) {
        const obj = await this.$axios.$post(buildUrl(null), data);
        commit('set', obj);
        return obj;
      },
      async update({ commit }, obj) {
        obj = await this.$axios.$put(buildUrl(obj.id), obj);
        commit('set', obj);
        return obj;
      },
      async partialUpdate({ commit }, { obj, fields = null }) {
        let updatedData = obj;
        if (fields !== null) {
          updatedData = pick(obj, fields.concat(['id']));
        }
        
        obj = await this.$axios.$patch(buildUrl(obj.id), updatedData);
        commit('set', obj);
        return obj;
      },
      async delete({ commit }, obj) {
        await this.$axios.$delete(buildUrl(obj.id));
        commit('remove', obj);
      }
    }
  }
}

export function updateObjectReactive(obj, vals) {
  for (const [k, v] of Object.entries(vals)) {
    if (isObject(v) && isObject(obj[k])) {
      updateObjectReactive(obj[k], v);
    } else {
      vueSet(obj, k, v);
    }
  }
}

export function uniqueName(baseName, existingNames) {
  let i = 1;
  while (true) {
    const name = baseName + i;
    if (!existingNames.includes(name)) {
      return name
    }
    i += 1;
  }
}
