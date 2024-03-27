import orderBy from "lodash/orderBy";
import pick from "lodash/pick";
import { groupNotes } from "@/stores/usernotes";
import type { PentestFinding, PentestProject, ProjectNote, ReportSection } from "~/utils/types";
import { scoreFromVector } from "~/utils/cvss";

export function sortFindings({ findings, projectType, overrideFindingOrder = false, topLevelFields = false }: {findings: PentestFinding[], projectType: ProjectType, overrideFindingOrder?: boolean, topLevelFields?: boolean}): PentestFinding[] {
  if (overrideFindingOrder || projectType.finding_ordering.length === 0) {
    return orderBy(findings, ['order', 'created']);
  } else {
    return orderBy(
      findings,
      projectType.finding_ordering.map(o => (finding: PentestFinding) => {
        const v = topLevelFields ? (finding as any)[o.field] : finding.data[o.field];
        const d = projectType.finding_fields[o.field];
        if (!d || d.type in [FieldDataType.LIST, FieldDataType.OBJECT, FieldDataType.USER] || Array.isArray(v) || typeof v === 'object') {
          // Sorting by field is unsupported
          return '';
        } else if (d.type === FieldDataType.CVSS) {
          return scoreFromVector(v) || 0;
        } else if (d.type === FieldDataType.CWE) {
          if (!v) {
            return -1;
          } 
          return Number(v.replace('CWE-'))
        } else if (d.type === FieldDataType.ENUM) {
          return d.choices!.findIndex(c => c.value === v);
        } else if (v !== null && v !== undefined) {
          return v;
        } else if (d.type === FieldDataType.NUMBER) {
          return 0;
        } else if (d.type === FieldDataType.BOOLEAN) {
          return false;
        } else {
          return '';
        }
      }).concat(f => f.created),
      projectType.finding_ordering.map(o => o.order).concat([SortOrder.ASC])
    );
  }
}

export const useProjectStore = defineStore('project', {
  state: () => ({
    data: {} as {
      [key: string]: {
        project: PentestProject|null,
        findings: PentestFinding[],
        sections: ReportSection[],
        // notes: ProjectNote[],
        getByIdSync: Promise<PentestProject> | null,
        notesCollabState: CollabStoreState<{ notes: {[key: string]: ProjectNote}}>,
      }
    },
  }),
  getters: {
    project() {
      return (projectId: string) => this.data[projectId]?.project;
    },
    findings() {
      return (projectId: string, { projectType = null as ProjectType|null } = {}) => {
        const projectState = this.data[projectId]
        let findings = projectState?.findings || [];
        if (projectState && projectType) {
          findings = sortFindings({
            findings,
            projectType,
            overrideFindingOrder: projectState.project!.override_finding_order,
          })
        }
        return findings;
      };
    },
    sections() {
      return (projectId: string) => this.data[projectId]?.sections || [];
    },
    notes() {
      return (projectId: string) => Object.values(this.data[projectId]?.notesCollabState.data.notes || {}) as ProjectNote[];
    },
    noteGroups() {
      return (projectId: string) => groupNotes(this.notes(projectId));
    },
  },
  actions: {
    clear() {
      this.data = {};
    },
    ensureExists(projectId: string, initialStoreData?: Object) {
      if (!(projectId in this.data)) {
        this.data[projectId] = {
          project: null as unknown as PentestProject,
          findings: [],
          sections: [],
          getByIdSync: null,
          notesCollabState: makeCollabStoreState({
            websocketPath: `/ws/pentestprojects/${projectId}/notes/`,
            initialData: { notes: {} },
            handleAdditionalWebSocketMessages: (msgData: any) => {
              const collabState = this.data[projectId].notesCollabState;
              if (msgData.type === CollabEventType.SORT && msgData.path === 'notes') {
                for (const note of Object.values(collabState.data.notes) as ProjectNote[]) {
                  const no = msgData.sort.find((n: ProjectNote) => n.id === note.id);
                  note.parent = no?.parent || null;
                  note.order = no?.order || 0;
                }
                return true;
              } else {
                return false;
              }
            }
          }),
          ...(initialStoreData || {})
        }
      }
      return this.data[projectId];
    },
    setProject(project: PentestProject) {
      const prev = { ...this.ensureExists(project.id) };
      const next = { ...prev };

      // Update project
      next.project = project;
      // Invalidate cached findings and section that contain inlined values of the project
      if (prev.project?.project_type !== next.project.project_type || prev.project?.language !== next.project.language) {
        next.findings = [];
        next.sections = [];
      }

      // Set inlined data from detail response
      if (Array.isArray((project as any).findings)) {
        next.findings = (project as any).findings;
      }
      if (Array.isArray((project as any).sections)) {
        next.sections = (project as any).sections;
      }

      this.data[project.id] = next;
      return this.data[project.id];
    },
    async fetchById(projectId: string): Promise<PentestProject> {
      const obj = await $fetch<PentestProject>(`/api/v1/pentestprojects/${projectId}/`, { method: 'GET' });
      return this.setProject(obj).project!;
    },
    async getById(projectId: string): Promise<PentestProject> {
      if (Array.isArray(projectId)) {
        projectId = projectId[0];
      }

      if (projectId in this.data && this.data[projectId].project) {
        return this.data[projectId].project!;
      } else if (projectId in this.data && this.data[projectId].getByIdSync) {
        return await this.data[projectId].getByIdSync!;
      } else {
        try {
          const getByIdSync = this.fetchById(projectId);
          this.ensureExists(projectId, { getByIdSync });
          return await getByIdSync;
        } finally {
          if (this.data[projectId]?.getByIdSync) {
            this.data[projectId].getByIdSync = null;
          }
        }
      }
    },
    async createProject(projectData: Object) {
      const proj = await $fetch<PentestProject>(`/api/v1/pentestprojects/`, {
        method: 'POST',
        body: projectData
      });
      return this.setProject(proj).project!;
    },
    async partialUpdateProject(project: PentestProject, fields?: string[]) {
      const proj = await $fetch<PentestProject>(`/api/v1/pentestprojects/${project.id}/`, {
        method: 'PATCH',
        body: fields ? pick(project, fields?.concat(['id'])) : project,
      });
      return this.setProject(proj).project!;
    },
    async deleteProject(project: PentestProject) {
      await $fetch(`/api/v1/pentestprojects/${project.id}/`, {
        method: 'DELETE'
      });
      if (project.id in this.data) {
        delete this.data[project.id];
      }
    },
    async copyProject(project: PentestProject) {
      const proj = await $fetch<PentestProject>(`/api/v1/pentestprojects/${project.id}/copy/`, {
        method: 'POST',
        body: {}
      });
      return this.setProject(proj).project!;
    },
    async setReadonly(project: PentestProject, readonly: boolean) {
      await $fetch(`/api/v1/pentestprojects/${project.id}/readonly/`, {
        method: 'PATCH',
        body: {
          readonly,
        }
      });
      this.ensureExists(project.id);
      this.data[project.id].project!.readonly = readonly;
    },
    async customizeDesign(project: PentestProject) {
      const res = await $fetch<{ project_type: string }>(`/api/v1/pentestprojects/${project.id}/customize-projecttype/`, {
        method: 'POST',
        body: {}
      });
      this.ensureExists(project.id);
      this.setProject({ ...this.data[project.id].project!, project_type: res.project_type });
    },
    async createFinding(project: PentestProject, findingData: Object) {
      const finding = await $fetch<PentestFinding>(`/api/v1/pentestprojects/${project.id}/findings/`, {
        method: 'POST',
        body: findingData,
      });
      this.ensureExists(project.id)
      this.data[project.id].findings.push(finding);
      return finding;
    },
    async createFindingFromTemplate(project: PentestProject, findingFromTemplateData: { template: string, template_language: string }) {
      const finding = await $fetch<PentestFinding>(`/api/v1/pentestprojects/${project.id}/findings/fromtemplate/`, {
        method: 'POST',
        body: findingFromTemplateData,
      });
      this.ensureExists(project.id)
      this.data[project.id].findings.push(finding);
      return finding;
    },
    setFinding(project: PentestProject, finding: PentestFinding) {
      this.ensureExists(project.id);
      const findings = this.data[project.id].findings;
      const findingIdx = findings.findIndex(f => f.id === finding.id)
      if (findingIdx !== -1) {
        findings[findingIdx] = finding;
      } else {
        findings.push(finding);
      }
      return finding;
    },
    async updateFinding(project: PentestProject, finding: PentestFinding) {
      finding = await $fetch<PentestFinding>(`/api/v1/pentestprojects/${project.id}/findings/${finding.id}/`, {
        method: 'PUT',
        body: finding
      });
      return this.setFinding(project, finding);
    },
    async deleteFinding(project: PentestProject, finding: PentestFinding) {
      await $fetch(`/api/v1/pentestprojects/${project.id}/findings/${finding.id}/`, {
        method: 'DELETE'
      });
      if (project.id in this.data) {
        this.data[project.id].findings = this.data[project.id].findings.filter(f => f.id !== finding.id);
      }
    },
    async sortFindings(project: PentestProject, findings: PentestFinding[]) {
      this.ensureExists(project.id);
      const orderedFindings = findings.map((f, idx) => ({ ...(this.data[project.id].findings.find(fs => fs.id === f.id) || f), order: idx + 1 }));
      this.data[project.id].findings = orderedFindings;
      const res = await $fetch<{ id: string; order: number }[]>(`/api/v1/pentestprojects/${project.id}/findings/sort/`, {
        method: 'POST',
        body: orderedFindings.map(f => ({ id: f.id, order: f.order })),
      });
      for (const finding of this.data[project.id].findings) {
        finding.order = res.find(f => f.id === finding.id)?.order || 0;
      }
    },
    async updateSection(project: PentestProject, section: ReportSection) {
      section = await $fetch<ReportSection>(`/api/v1/pentestprojects/${project.id}/sections/${section.id}/`, {
        method: 'PUT',
        body: section,
      });
      return this.setSection(project, section);
    },
    setSection(project: PentestProject, section: ReportSection) {
      this.ensureExists(project.id);
      const sections = this.data[project.id].sections;
      const sectionIdx = sections.findIndex(s => s.id === section.id)
      if (sectionIdx !== -1) {
        sections[sectionIdx] = section;
      } else {
        sections.push(section);
      }
      return section;
    },
    async createNote(project: PentestProject, note: ProjectNote) {
      note = await $fetch<ProjectNote>(`/api/v1/pentestprojects/${project.id}/notes/`, {
        method: 'POST',
        body: note
      });
      this.ensureExists(project.id);
      this.data[project.id].notesCollabState.data.notes[note.id] = note;
      return note;
    },
    async deleteNote(project: PentestProject, note: ProjectNote) {
      await $fetch(`/api/v1/pentestprojects/${project.id}/notes/${note.id}/`, {
        method: 'DELETE'
      });
      if (project.id in this.data) {
        delete this.data[project.id].notesCollabState.data.notes[note.id];
      }
    },
    async sortNotes(project: PentestProject, noteGroups: NoteGroup<ProjectNote>) {
      this.ensureExists(project.id)
      const notes = [] as ProjectNote[];
      sortNotes(noteGroups, (n) => {
        notes.push(n);
      });
      this.data[project.id].notesCollabState.data.notes = Object.fromEntries(notes.map(n => [n.id, n]));
      await $fetch<{id: string; parent: string|null; order: number}[]>(`/api/v1/pentestprojects/${project.id}/notes/sort/`, {
        method: 'POST',
        body: notes.map(n => pick(n, ['id', 'parent', 'order']))
      });
    },
    async fetchNotes(project: PentestProject) {
      const notes = await $fetch<ProjectNote[]>(`/api/v1/pentestprojects/${project.id}/notes/`, { method: 'GET' });
      this.ensureExists(project.id);
      this.data[project.id].notesCollabState.data.notes = Object.fromEntries(notes.map(n => [n.id, n]));
      return notes;
    },
    useNotesCollab(project: PentestProject, noteId?: string) {
      this.ensureExists(project.id);

      const collabState = this.data[project.id].notesCollabState;
      const collab = useCollab(collabState);

      const hasEditPermissions = computed(() => !project.readonly);

      return {
        ...collab,
        collabProps: computed(() => collabSubpath(collab.collabProps.value, noteId ? `notes.${noteId}` : null)),
        hasEditPermissions,
        readonly: computed(() => !hasEditPermissions.value || collabState.connectionState !== CollabConnectionState.OPEN),
      };
    },
  },
})
