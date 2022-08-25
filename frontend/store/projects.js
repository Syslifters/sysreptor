import Vue from "vue";
import * as cvss from "@/utils/cvss.js";
import { updateObjectReactive } from "~/utils/state";

export const state = () => ({
  data: {},
});

function ensureExists(state, projectId, prop, val = null) {
  if (!(projectId in state.data)) {
    Vue.set(state.data, projectId, {});
  }
  if (!(prop in state.data[projectId])) {
    Vue.set(state.data[projectId], prop, val);
  }
  return state.data[projectId][prop];
}

export const mutations = {
  set(state, obj) {
    ensureExists(state, obj.id, 'project');
    state.data[obj.id].project = obj;
  },
  delete(state, obj) {
    if (obj.id in state.data) {
      Vue.delete(state.data, obj.id);
    }
  },
  setFinding(state, { projectId, finding }) {
    const existingFinding = ensureExists(state, projectId, 'findings', []).find(f => f.id === finding.id);
    if (existingFinding) {
      updateObjectReactive(existingFinding, finding);
    } else {
      state.data[projectId].findings.push(finding);
    }
  },
  removeFinding(state, { projectId, findingId }) {
    if (!(projectId in state.data)) {
      return;
    }
    const findings = state.data[projectId].findings || [];
    const existingFindingIdx = findings.findIndex(f => f.id === findingId);
    if (existingFindingIdx !== -1) {
      findings.splice(existingFindingIdx, 1);
    }
  },
  setFindings(state, { projectId, findings }) {
    ensureExists(state, projectId, 'findings', []);
    // Update/add findings
    for (const finding of findings) {
      this.commit('projects/setFinding', { projectId, finding });
    }
    // Remove deleted findings
    for (const finding of state.data[projectId].findings.filter(f => !findings.map(f2 => f2.id).includes(f.id))) {
      this.commit('projects/removeFinding', { projectId, findingId: finding.id });
    }
  },
  setSection(state, { projectId, section }) {
    const existingSection = ensureExists(state, projectId, 'sections', []).find(f => f.id === section.id);
    if (existingSection) {
      updateObjectReactive(existingSection, section);
    } else {
      state.data[projectId].sections.push(section);
    }
  },
  setSections(state, { projectId, sections }) {
    ensureExists(state, projectId, 'sections', []);
    // Update/add sections
    for (const section of sections) {
      this.commit('projects/setSection', { projectId, section });
    }
    // Remove deleted sections
    for (const section of state.data[projectId].sections.filter(s => !sections.map(s2 => s2.id).includes(s.id))) {
      const sects = state.data[projectId].sections || [];
      const existingSectionIdx = sects.findIndex(s => s.id === section.id);
      if (existingSectionIdx !== -1) {
        sects.splice(existingSectionIdx, 1);
      }
    }
  }
};

export const actions = {
  async fetchById({ commit }, projectId) {
    const obj = await this.$axios.$get(`/pentestprojects/${projectId}/`);
    commit('set', obj);
    return obj;
  },
  async getById({ dispatch, state }, projectId) {
    if (projectId in state.data && state.data[projectId].project) {
      return state.data[projectId].project;
    }
    return await dispatch('fetchById', projectId);
  },
  async fetchFindings({ commit, state }, projectId) {
    const findings = await this.$axios.$get(`/pentestprojects/${projectId}/findings/`);
    commit('setFindings', { projectId, findings });
    return findings;
  },
  async getFindings({ dispatch, state }, projectId) {
    if (projectId in state.data && state.data[projectId].findings) {
      return state.data[projectId].findings;
    }
    return await dispatch('fetchFindings', projectId);
  },
  async fetchSections({ commit }, projectId) {
    const sections = await this.$axios.$get(`/pentestprojects/${projectId}/sections/`);
    commit('setSections', { projectId, sections });
    return sections;
  },
  async getSections({ dispatch, state }, projectId) {
    if (projectId in state.data && state.data[projectId].sections) {
      return state.data[projectId].sections;
    }
    return await dispatch('fetchSections', projectId);
  },
  async create({ commit }, project) {
    const obj = await this.$axios.$post(`/pentestprojects/`, project);
    commit('set', obj);
    return obj;
  },
  async update({ commit, state }, project) {
    const obj = await this.$axios.$put(`/pentestprojects/${project.id}/`, project);
    if (obj.id in state.data) {
      commit('set', obj);
    }
    return obj;
  },
  async delete({ commit }, project) {
    await this.$axios.$delete(`/pentestprojects/${project.id}/`);
    commit('delete', project);
  },
  async updateFinding({ commit }, { projectId, finding }) {
    const updatedFinding = await this.$axios.$put(`/pentestprojects/${projectId}/findings/${finding.id}/`, finding);
    commit('setFinding', { projectId, finding: updatedFinding });
    return updatedFinding;
  },
  async createFinding({ commit }, projectId) {
    const finding = await this.$axios.$post(`/pentestprojects/${projectId}/findings/`, {
      data: {
        title: 'New finding',
      },
    });
    commit('setFinding', { projectId, finding });
    return finding;
  },
  async createFindingFromTemplate({ commit }, { projectId, templateId }) {
    const finding = await this.$axios.$post(`/pentestprojects/${projectId}/findings/fromtemplate/`, {
      template: templateId,
    });
    commit('setFinding', { projectId, finding });
    return finding;
  },
  async deleteFinding({ commit }, { projectId, findingId }) {
    await this.$axios.$delete(`/pentestprojects/${projectId}/findings/${findingId}/`);
    commit('removeFinding', { projectId, findingId });
  },
  async updateSection({ commit }, { projectId, section }) {
    const updatedSection = await this.$axios.$put(`/pentestprojects/${projectId}/sections/${section.id}/`, section);
    commit('setSection', { projectId, section: updatedSection });
    return updatedSection;
  },
}

export const getters = {
  findings: state => (projectId) => {
    const project = state.data[projectId];
    if (!project) {
      return [];
    }
    return Array.from(project.findings || [])
      .sort((a, b) => cvss.scoreFromVector(b.data.cvss) - cvss.scoreFromVector(a.data.cvss));
  },
  sections: state => (projectId) => {
    const project = state.data[projectId];
    if (!project) {
      return [];
    }
    return state.data[projectId].sections || [];
  }
}
