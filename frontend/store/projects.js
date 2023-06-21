import { set as vueSet, del as vueDel } from "vue";
import { omit, merge, pick } from "lodash";
import { groupNotes, sortNotes } from "./usernotes";
import { updateObjectReactive } from "~/utils/state";
import { sortFindings } from "~/utils/other";

export const state = () => ({
  data: {},
});

function ensureExists(state, projectId, prop, val = null) {
  if (!(projectId in state.data)) {
    vueSet(state.data, projectId, {});
  }
  if (!(prop in state.data[projectId])) {
    vueSet(state.data[projectId], prop, val);
  }
  return state.data[projectId][prop];
}

export const mutations = {
  set(state, obj) {
    ensureExists(state, obj.id, 'project');
    
    // Invalidate cached findings and section that contain inlined values of the project
    const oldProjectType = state.data[obj.id]?.project?.project_type;
    const oldLanguage = state.data[obj.id]?.project?.language;
    if ((oldProjectType && oldProjectType !== obj.project_type) || (oldLanguage && oldLanguage !== obj.language)) {
      vueDel(state.data[obj.id], 'findings');
      vueDel(state.data[obj.id], 'sections');
    }

    state.data[obj.id].project = obj;
  },
  setGetByIdSync(state, { projectId, sync }) {
    ensureExists(state, projectId, 'getByIdSync', sync);
  },
  update(state, obj) {
    if (!(obj.id in state.data) || !state.data[obj.id].project) {
      return;
    }

    updateObjectReactive(state.data[obj.id].project, obj);
  },
  remove(state, obj) {
    if (obj.id in state.data) {
      vueDel(state.data, obj.id);
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
  },
  setNote(state, { projectId, note }) {
    const existingNote = ensureExists(state, projectId, 'notes', []).find(n => n.id === note.id);
    if (existingNote) {
      updateObjectReactive(existingNote, note);
    } else {
      state.data[projectId].notes.push(note);
    }
  },
  removeNote(state, { projectId, noteId }) {
    if (!(projectId in state.data)) {
      return;
    }
    const notes = state.data[projectId].notes || [];
    const existingNoteIdx = notes.findIndex(f => f.id === noteId);
    if (existingNoteIdx !== -1) {
      notes.splice(existingNoteIdx, 1);
    }
  },
  setNotes(state, { projectId, notes }) {
    ensureExists(state, projectId, 'notes', []);
    // Update/add notes
    for (const note of notes) {
      this.commit('projects/setNote', { projectId, note });
    }
    // Remove deleted notes
    for (const note of state.data[projectId].notes.filter(n => !notes.map(n2 => n2.id).includes(n.id))) {
      this.commit('projects/removeNote', { projectId, noteId: note.id });
    }
  },
};

export const actions = {
  async fetchById({ commit }, projectId) {
    const obj = await this.$axios.$get(`/pentestprojects/${projectId}/`);
    commit('set', obj);
    return obj;
  },
  async getById({ dispatch, state, commit }, projectId) {
    if (projectId in state.data && state.data[projectId].project) {
      return state.data[projectId].project;
    } else if (projectId in state.data && state.data[projectId].getByIdSync) {
      return await state.data[projectId].getByIdSync;
    } else {
      try {
        const fetchById = dispatch('fetchById', projectId);
        commit('setGetByIdSync', { projectId, sync: fetchById });
        return await fetchById;
      } finally {
        commit('setGetByIdSync', { projectId, sync: null });
      }
    }
  },
  async fetchFindings({ commit }, projectId) {
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
  async fetchNotes({ commit }, projectId) {
    const notes = await this.$axios.$get(`/pentestprojects/${projectId}/notes/`);
    commit('setNotes', { projectId, notes });
    return notes;
  },
  async getNotes({ dispatch, state }, projectId) {
    if (projectId in state.data && state.data[projectId].notes) {
      return state.data[projectId].notes;
    }
    return await dispatch('fetchNotes', projectId);
  },
  async create({ commit }, project) {
    const obj = await this.$axios.$post(`/pentestprojects/`, project);
    commit('set', obj);
    return obj;
  },
  async update({ commit }, project) {
    const obj = await this.$axios.$put(`/pentestprojects/${project.id}/`, project);
    commit('set', obj);
    return obj;
  },
  async delete({ commit }, project) {
    await this.$axios.$delete(`/pentestprojects/${project.id}/`);
    commit('remove', project);
  },
  async copy({ commit }, data) {
    const copied = await this.$axios.$post(`/pentestprojects/${data.id}/copy/`, omit(data, ['id']));
    commit('set', copied);
    return copied;
  },
  async setReadonly({ commit }, { projectId, readonly }) {
    const res = await this.$axios.$patch(`/pentestprojects/${projectId}/readonly/`, {
      readonly,
    });
    commit('update', { id: projectId, ...res });
  },
  async customizeDesign({ commit }, { projectId }) {
    const res = await this.$axios.$post(`/pentestprojects/${projectId}/customize-projecttype/`, {});
    commit('update', { id: projectId, ...res });
  },
  async updateFinding({ commit }, { projectId, finding }) {
    const updatedFinding = await this.$axios.$put(`/pentestprojects/${projectId}/findings/${finding.id}/`, finding);
    commit('setFinding', { projectId, finding: updatedFinding });
    return updatedFinding;
  },
  async createFinding({ commit }, { projectId, finding = {} }) {
    const newFinding = await this.$axios.$post(`/pentestprojects/${projectId}/findings/`, merge({ data: {} }, finding));
    commit('setFinding', { projectId, finding: newFinding });
    return newFinding;
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
  async createNote({ commit }, { projectId, note = {} }) {
    const newNote = await this.$axios.$post(`/pentestprojects/${projectId}/notes/`, note);
    commit('setNote', { projectId, note: newNote });
    return newNote;
  },
  async updateNote({ commit }, { projectId, note }) {
    const updatedNote = await this.$axios.$put(`/pentestprojects/${projectId}/notes/${note.id}/`, note);
    commit('setNote', { projectId, note: updatedNote });
    return updatedNote;
  },
  async partialUpdateNote({ commit }, { projectId, note, fields }) {
    let updatedData = note;
    if (fields !== null) {
      updatedData = pick(note, fields.concat(['id']));
    }
    note = await this.$axios.$patch(`/pentestprojects/${projectId}/notes/${note.id}/`, updatedData);
    commit('setNote', { projectId, note });
    return note;
  },
  async deleteNote({ commit }, { projectId, noteId }) {
    await this.$axios.$delete(`/pentestprojects/${projectId}/notes/${noteId}/`);
    commit('removeNote', { projectId, noteId });
  },
  async sortNotes({ commit, getters }, { projectId, noteGroups }) {
    sortNotes(noteGroups, note => commit('setNote', { projectId, note }));
    await this.$axios.$post(`/pentestprojects/${projectId}/notes/sort/`, getters.notes(projectId));
  }
}

export const getters = {
  project: state => (projectId) => {
    return state.data[projectId]?.project;
  },
  findings: state => (projectId) => {
    return sortFindings(state.data[projectId]?.findings || []);
  },
  sections: state => (projectId) => {
    return state.data[projectId]?.sections || [];
  },
  notes: state => (projectId) => {
    return state.data[projectId]?.notes || [];
  },
  noteGroups: state => (projectId) => {
    return groupNotes(state.data[projectId]?.notes || []);
  },
}
