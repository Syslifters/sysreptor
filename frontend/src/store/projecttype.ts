import pick from 'lodash/pick';
import { FieldDefinitionDict, ProjectType, ProjectTypeScope } from "~/utils/types";

export const useProjectTypeStore = defineStore('projecttype', {
  state: () => ({
    data: {} as {
      [key: string]: ProjectType
    },
    predefinedFindingFields: null as FieldDefinitionDict|null,
  }),
  actions: {
    clear() {
      this.data = {};
    },
    async fetchById(id: string) {
      this.data[id] = await $fetch<ProjectType>(`/api/v1/projecttypes/${id}/`, { method: 'GET' });
      return this.data[id];
    },
    async getById(id: string) {
      if (id in this.data) {
        return this.data[id];
      }
      return await this.fetchById(id);
    },
    async create(projectType: ProjectType) {
      const obj = await $fetch<ProjectType>('/api/v1/projecttypes/', {
        method: 'GET',
        body: projectType
      });
      this.data[obj.id] = obj;
      return this.data[obj.id];
    },
    async partialUpdate(projectType: ProjectType, fields?: string[]) {
      const updatedData = fields ? pick(projectType, fields.concat(['id'])) : projectType;
      this.data[projectType.id] = await $fetch<ProjectType>(`/api/v1/projecttypes/${projectType.id}/`, {
        method: 'PATCH',
        body: updatedData
      });
      return this.data[projectType.id];
    },
    async delete(projectType: ProjectType) {
      await $fetch(`/api/v1/projecttypes/${projectType.id}/`, {
        method: 'DELETE'
      });
      delete this.data[projectType.id];
    },
    async copy(projectType: {id: string, name?: string, scope?: ProjectTypeScope }) {
      const obj = await $fetch<ProjectType>(`/api/v1/projecttypes/${projectType.id}/copy/`, {
        method: 'POST',
        body: projectType
      });
      this.data[obj.id] = obj;
      return this.data[obj.id];
    },
    async getPredefinedFindingFields() {
      if (!this.predefinedFindingFields) {
        this.predefinedFindingFields = await $fetch('/api/v1/projecttypes/predefinedfields/findings/', { method: 'GET' });
      }
      return this.predefinedFindingFields!;
    },
  }
});
