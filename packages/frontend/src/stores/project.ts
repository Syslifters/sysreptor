import { orderBy, pick, set, isObject, isEqual, sortBy } from "lodash-es";
import { groupNotes } from "@/stores/usernotes";
import { useCollabSubpaths, collabSubpath, type CollabPropType, type Comment, type CommentAnswer, type CommentStatus, type PentestFinding, type PentestProject, type ProjectNote, type ProjectType, type ReportSection } from "#imports";

export function useFindingFieldValueSuggestions(findings: MaybeRefOrGetter<Record<string, PentestFinding>>, projectType: MaybeRefOrGetter<ProjectType>) {
  const findingsRef = toRef(findings);
  const projectTypeRef = toRef(projectType);

  function getValue(path: string, definition: FieldDefinition, value: any): { path: string, value: any }[] {
    if (definition.type === FieldDataType.LIST && Array.isArray(value)) {
      return value.flatMap(v => getValue(`${path}[]`, definition.items!, v));
    } else if (definition.type === FieldDataType.OBJECT && isObject(value)) {
      return (definition.properties || []).flatMap(def => getValue(`${path}.${def.id}`, def, (value as any)[def.id]));
    } else if (definition.type === FieldDataType.COMBOBOX && value) {
      return [{ path, value }];
    }
    return [];
  }

  const cachedValue = ref(new Map<string, string[]>());
  watchEffect(() => {
    const newValue = new Map<string, string[]>();
    for (const finding of Object.values(findingsRef.value)) {
      for (const fieldDefinition of projectTypeRef.value.finding_fields) {
        for (const { path, value } of getValue(fieldDefinition.id, fieldDefinition, finding.data[fieldDefinition.id])) {
          if (!newValue.has(path)) {
            newValue.set(path, []);
          }
          const values = newValue.get(path)!;
          if (!values.includes(value)) {
            values.push(value);
          }
        }
      }
    }

    // Remove old paths
    for (const path of cachedValue.value.keys()) {
      if (!newValue.has(path)) {
        cachedValue.value.delete(path);
      }
    }
    // Set new paths / update changed values
    for (const [path, values] of newValue.entries()) {
      if (!isEqual(values, cachedValue.value.get(path))) {
        cachedValue.value.set(path, values);
      }
    }
  })
  
  return cachedValue;
}

export const useProjectStore = defineStore('project', {
  state: () => ({
    data: {} as Record<string, {
      project: PentestProject|null,
      getByIdSync: Promise<PentestProject> | null,
      notesCollabState: CollabStoreState<{ notes: Record<string, ProjectNote>}>,
      reportingCollabState: CollabStoreState<{ 
        project: {id: string, project_type: string, override_finding_order: boolean}, 
        findings: Record<string, PentestFinding>, 
        sections: Record<string, ReportSection>, 
        comments: Record<string, Comment>,
      }>,
    }>,
  }),
  getters: {
    project() {
      return (projectId: string) => this.data[projectId]?.project;
    },
    findings() {
      return (projectId: string, { projectType = null as ProjectType|null } = {}) => {
        const projectState = this.data[projectId]
        let findings = sortBy(Object.values(this.data[projectId]?.reportingCollabState.data.findings || {}), ['id']);
        // Sort findings
        if (projectState && projectType) {
          findings = groupFindings({
            findings,
            projectType,
            overrideFindingOrder: projectState.project!.override_finding_order,
          }).flatMap(f => f.findings);
        }
        return findings;
      };
    },
    sections() {
      return (projectId: string, { projectType = null as ProjectType|null } = {}) => {
        let sections = sortBy(Object.values(this.data[projectId]?.reportingCollabState.data.sections || {}), ['id']);
        // Sort sections
        if (projectType) {
          sections = orderBy(sections, [s => projectType.report_sections.findIndex(rs => rs.id === s.id)]);
        }
        return sections;
      };
    },
    notes() {
      return (projectId: string) => Object.values(this.data[projectId]?.notesCollabState.data.notes || {});
    },
    noteGroups() {
      return (projectId: string) => groupNotes(this.notes(projectId));
    },
    comments() {
      return (projectId: string, options: {projectType: ProjectType, findingId?: string, sectionId?: string}) => {
        // Filter and sort comments
        const collabState = this.data[projectId]?.reportingCollabState;
        let commentData = Object.values(collabState?.data.comments || {}).map(c => ({ 
          ...c, 
          collabPath: collabState!.apiPath + c.path,
        } as Comment));
        if (options.findingId) {
          const basePath = `findings.${options.findingId}.data.`;
          commentData = orderBy(
            commentData.filter(c => c.path.startsWith(basePath)), 
            [(c) => {
              const fieldId = c.path.slice(basePath.length).split('.')?.[0];
              return options.projectType?.finding_fields.map(f => f.id).indexOf(fieldId!)
            }, 'path', 'created']
          );
        } else if (options.sectionId) {
          const basePath = `sections.${options.sectionId}.data.`;
          commentData = orderBy(
            commentData.filter(c => c.path.startsWith(basePath)),
            [(c) => {
              const fieldId = c.path.slice(basePath.length).split('.')?.[0];
              const sectionFields = options.projectType?.report_sections.find(s => s.id === options.sectionId)?.fields || [];
              return sectionFields.map(f => f.id).indexOf(fieldId!)
            }, 'path', 'created']
          );
        } else {
          commentData = [];
        }
        return commentData;
      };
    },
  },
  actions: {
    ensureExists(projectId: string, initialStoreData?: object) {
      if (!(projectId in this.data)) {
        this.data[projectId] = {
          project: null as unknown as PentestProject,
          getByIdSync: null,
          notesCollabState: makeCollabStoreState({
            apiPath: `/api/ws/pentestprojects/${projectId}/notes/`,
            initialData: { notes: {} as Record<string, ProjectNote> },
            initialPath: 'notes',
            handleAdditionalWebSocketMessages: (msgData: any, collabState) => {
              if (msgData.type === CollabEventType.SORT && msgData.path === 'notes') {
                for (const note of Object.values(collabState.data.notes)) {
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
          reportingCollabState: makeCollabStoreState({
            apiPath: `/api/ws/pentestprojects/${projectId}/reporting/`,
            initialData: { 
              project: {} as any, 
              findings: {} as Record<string, PentestFinding>, 
              sections: {} as Record<string, ReportSection>, 
              comments: {} as Record<string, Comment>,
            },
            handleAdditionalWebSocketMessages: (msgData: any, collabState) => {
              if (msgData.type === CollabEventType.SORT && msgData.path === 'findings') {
                for (const finding of Object.values(collabState.data.findings)) {
                  const fo = msgData.sort.find((n: PentestFinding) => n.id === finding.id);
                  finding.order = fo?.order || 0;
                }
                return true;
              } else if (msgData.type === CollabEventType.UPDATE_KEY && msgData.path?.startsWith('project.')) {
                set(this.data[projectId]!.project || {} as object, msgData.path.slice('project.'.length), msgData.value);
                if (msgData.path === 'project.project_type') {
                  // Reload page on project_type changed to apply the new field definition
                  this.useReportingCollab({ project: this.data[projectId]!.project! }).disconnect();
                  reloadNuxtApp({ force: true });
                }

                // Let the default handler update the key in store state
                return false;
              } else {
                return false;
              }
            }
          }),
          ...(initialStoreData || {})
        }
      }
      return this.data[projectId]!;
    },
    setProject(project: PentestProject) {
      this.ensureExists(project.id);
      this.data[project.id]!.project = project;
      return this.data[project.id]!.project!;
    },
    async fetchById(projectId: string): Promise<PentestProject> {
      const obj = await $fetch<PentestProject>(`/api/v1/pentestprojects/${projectId}/`, { method: 'GET' });
      return this.setProject(obj);
    },
    async getById(projectId: string): Promise<PentestProject> {
      if (Array.isArray(projectId)) {
        projectId = projectId[0];
      }

      if (projectId in this.data && this.data[projectId]!.project) {
        return this.data[projectId]!.project!;
      } else if (projectId in this.data && this.data[projectId]!.getByIdSync) {
        return await this.data[projectId]!.getByIdSync!;
      } else {
        try {
          const getByIdSync = this.fetchById(projectId);
          this.ensureExists(projectId, { getByIdSync });
          return await getByIdSync;
        } finally {
          if (this.data[projectId]?.getByIdSync) {
            this.data[projectId]!.getByIdSync = null;
          }
        }
      }
    },
    async createProject(projectData: object) {
      const proj = await $fetch<PentestProject>(`/api/v1/pentestprojects/`, {
        method: 'POST',
        body: projectData
      });
      return this.setProject(proj);
    },
    async partialUpdateProject(project: PentestProject, fields?: string[]) {
      const proj = await $fetch<PentestProject>(`/api/v1/pentestprojects/${project.id}/`, {
        method: 'PATCH',
        body: fields ? pick(project, fields?.concat(['id'])) : project,
      });
      return this.setProject(proj);
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
      return this.setProject(proj);
    },
    async setReadonly(project: PentestProject, readonly: boolean) {
      await $fetch(`/api/v1/pentestprojects/${project.id}/readonly/`, {
        method: 'PATCH',
        body: {
          readonly,
        }
      });
      this.ensureExists(project.id);
      this.data[project.id]!.project!.readonly = readonly;
    },
    async customizeDesign(project: PentestProject) {
      const res = await $fetch<{ project_type: string }>(`/api/v1/pentestprojects/${project.id}/customize-projecttype/`, {
        method: 'POST',
        body: {}
      });
      this.ensureExists(project.id);
      this.setProject({ ...this.data[project.id]!.project!, project_type: res.project_type });
    },
    async createFinding(project: PentestProject, findingData: Partial<PentestFinding>) {
      const finding = await $fetch<PentestFinding>(`/api/v1/pentestprojects/${project.id}/findings/`, {
        method: 'POST',
        body: findingData,
      });
      this.ensureExists(project.id)
      this.data[project.id]!.reportingCollabState.data.findings[finding.id] = finding;
      return finding;
    },
    async createFindingFromTemplate(project: PentestProject, findingFromTemplateData: { template: string, template_language: string }) {
      const finding = await $fetch<PentestFinding>(`/api/v1/pentestprojects/${project.id}/findings/fromtemplate/`, {
        method: 'POST',
        body: findingFromTemplateData,
      });
      this.ensureExists(project.id)
      this.data[project.id]!.reportingCollabState.data.findings[finding.id] = finding;
      return finding;
    },
    async copyFinding(project: PentestProject, finding: PentestFinding) {
      // Copy only finding data, reset metadata fields
      return await this.createFinding(project, {
        data: finding.data,
      })
    },
    async deleteFinding(project: PentestProject, finding: PentestFinding) {
      await $fetch(`/api/v1/pentestprojects/${project.id}/findings/${finding.id}/`, {
        method: 'DELETE'
      });
      if (project.id in this.data) {
        delete this.data[project.id]!.reportingCollabState.data.findings[finding.id];
      }
    },
    async sortFindings(project: PentestProject, findings: PentestFinding[]) {
      this.ensureExists(project.id);
      const orderedFindings = findings.map((f, idx) => ({ ...(this.findings(project.id).find(fs => fs.id === f.id) || f), order: idx + 1 }));
      this.data[project.id]!.reportingCollabState.data.findings = Object.fromEntries(orderedFindings.map(f => [f.id, f]));
      await $fetch<{ id: string; order: number }[]>(`/api/v1/pentestprojects/${project.id}/findings/sort/`, {
        method: 'POST',
        body: orderedFindings.map(f => ({ id: f.id, order: f.order })),
      });
    },
    async deleteComment(project: PentestProject, comment: Comment) {
      await $fetch(`/api/v1/pentestprojects/${project.id}/comments/${comment.id}/`, {
        method: 'DELETE'
      });
      if (project.id in this.data) {
        delete this.data[project.id]!.reportingCollabState.data.comments[comment.id];
      }
    },
    async updateComment(project: PentestProject, comment: Partial<Comment>) {
      const obj = await $fetch<Comment>(`/api/v1/pentestprojects/${project.id}/comments/${comment.id}/`, {
        method: 'PATCH',
        body: comment,
      });
      if (project.id in this.data) {
        this.data[project.id]!.reportingCollabState.data.comments[obj.id] = {
          ...obj,
          text_range: this.data[project.id]?.reportingCollabState?.data.comments[obj.id]?.text_range || obj.text_range,
        }
      }
    },
    async resolveComment(project: PentestProject, comment: Comment, data: { status: CommentStatus }) {
      await $fetch(`/api/v1/pentestprojects/${project.id}/comments/${comment.id}/resolve/`, {
        method: 'POST',
        body: data,
      });
    },
    async createCommentAnswer(project: PentestProject, comment: Comment, answer: CommentAnswer) {
      await $fetch(`/api/v1/pentestprojects/${project.id}/comments/${comment.id}/answers/`, {
        method: 'POST',
        body: answer
      });
    },
    async updateCommentAnswer(project: PentestProject, comment: Comment, answer: CommentAnswer) {
      await $fetch(`/api/v1/pentestprojects/${project.id}/comments/${comment.id}/answers/${answer.id}/`, {
        method: 'PATCH',
        body: answer
      });
    },
    async deleteCommentAnswer(project: PentestProject, comment: Comment, answer: CommentAnswer) {
      await $fetch(`/api/v1/pentestprojects/${project.id}/comments/${comment.id}/answers/${answer.id}/`, {
        method: 'DELETE'
      });
      const commentData = this.data[project.id]?.reportingCollabState.data.comments[comment.id];
      if (commentData) {
        commentData.answers = commentData.answers.filter(a => a.id !== answer.id);
      }
    },
    async createNote(project: PentestProject, note: Partial<ProjectNote>) {
      const newNote = await $fetch<ProjectNote>(`/api/v1/pentestprojects/${project.id}/notes/`, {
        method: 'POST',
        body: note
      });
      this.ensureExists(project.id);
      this.data[project.id]!.notesCollabState.data.notes[newNote.id] = newNote;
      return newNote;
    },
    async deleteNote(project: PentestProject, note: ProjectNote) {
      await $fetch(`/api/v1/pentestprojects/${project.id}/notes/${note.id}/`, {
        method: 'DELETE'
      });
      if (project.id in this.data) {
        delete this.data[project.id]!.notesCollabState.data.notes[note.id];
      }
    },
    async sortNotes(project: PentestProject, noteGroups: NoteGroup<ProjectNote>) {
      this.ensureExists(project.id)
      const notes = [] as ProjectNote[];
      sortNotes(noteGroups, (n) => {
        notes.push(n);
      });
      this.data[project.id]!.notesCollabState.data.notes = Object.fromEntries(notes.map(n => [n.id, n]));
      await $fetch<{id: string; parent: string|null; order: number}[]>(`/api/v1/pentestprojects/${project.id}/notes/sort/`, {
        method: 'POST',
        body: notes.map(n => pick(n, ['id', 'parent', 'order']))
      });
    },
    useNotesCollab(options: { project: PentestProject, noteId?: string }) {
      this.ensureExists(options.project.id);

      const collabState = this.data[options.project.id]!.notesCollabState;
      const collab = useCollab(collabState);
      const collabProps = computed<CollabPropType>((oldValue) => collabSubpath(
        collab.collabProps.value, 
        options.noteId ? `notes.${options.noteId}` : null, 
        oldValue
      ))

      const apiSettings = useApiSettings();
      const auth = useAuth();
      const hasLock = ref(true);
      if (options.noteId && !apiSettings.isProfessionalLicense) {
        hasLock.value = false;
        watch(() => collabProps.value.clients, () => {
          if (!hasLock.value && collabProps.value.clients.filter(c => c.user?.id !== auth.user.value?.id).length === 0) {
            hasLock.value = true;
          }
        }, { immediate: true });
      }

      async function connect() {
        if (options.project.readonly) {
          return await collab.connect({ connectionType: CollabConnectionType.HTTP_READONLY });
        }
        return await collab.connect();
      }

      return {
        ...collab,
        collabProps,
        hasLock,
        readonly: computed(() => collab.readonly.value || !hasLock.value),
        connect,
      };
    },
    useReportingCollab(options: { project: MaybeRefOrGetter<PentestProject>, projectType?: MaybeRefOrGetter<ProjectType>, findingId?: string, sectionId?: string }) {
      const project = toValue(options.project);
      const projectType = toValue(options.projectType);
      
      this.ensureExists(project.id);

      const collabState = this.data[project.id]!.reportingCollabState;
      const collab = useCollab(collabState);
      const collabProps = computed<CollabPropType>((oldValue) => collabSubpath(
        collab.collabProps.value, 
        options.findingId ? `findings.${options.findingId}` : options.sectionId ? `sections.${options.sectionId}` : null,
        oldValue
      ));
      const subpathNames = 
        (projectType && options.findingId) ? projectType.finding_fields.map(f => `data.${f.id}`).concat(['status', 'assignee']) :
        (projectType && options.sectionId) ? projectType.report_sections.flatMap(s => s.fields).map(f => `data.${f.id}`).concat(['status', 'assignee']) :
        [];
      const collabSubpathProps = useCollabSubpaths(collabProps, subpathNames);

      const apiSettings = useApiSettings();
      const auth = useAuth();
      const hasLock = ref(true);
      if ((options.findingId || options.sectionId) && !apiSettings.isProfessionalLicense) {
        hasLock.value = false;
        watch(() => collabProps.value.clients.length, () => {
          if (!hasLock.value && collabProps.value.clients.filter(c => c.user?.id !== auth.user.value?.id).length === 0) {
            hasLock.value = true;
          }
        }, { immediate: true });
      }

      async function connect() {
        if (toValue(options.project).readonly) {
          return await collab.connect({ connectionType: CollabConnectionType.HTTP_READONLY });
        }
        return await collab.connect();
      }

      return {
        ...collab,
        collabProps,
        collabSubpathProps,
        hasLock,
        readonly: computed(() => collab.readonly.value || !hasLock.value),
        connect,
      };
    },
  },
})
