import sortBy from "lodash/sortBy";
import type { FieldDefinition, FieldDefinitionDict, FindingTemplate } from "~/utils/types";

export const useTemplateStore = defineStore('templates', {
  state: () => ({
    fieldDefinition: null as FieldDefinitionDict|null,
    getFieldDefinitionSync: null as Promise<FieldDefinitionDict>|null,
  }),
  getters: {
    fieldDefinitionList(): (FieldDefinition & { id: string; visible: boolean })[] {
      if (!this.fieldDefinition) {
        return [];
      }

      const fieldFilterHiddenFields = useLocalSettings().templateFieldFilterHiddenFields;
      return sortBy(
        Object.keys(this.fieldDefinition).map(id => ({ id, visible: !fieldFilterHiddenFields.includes(id), ...this.fieldDefinition![id] })),
        [(d) => {
          const originOrder = { core: 1, predefined: 2, custom: 3 };
          return originOrder[d.origin] || 10;
        }]);
    }
  },
  actions: {
    clear() {
      // Nothing to clear
    },
    async create(template: FindingTemplate) {
      return await $fetch<FindingTemplate>(`/api/v1/findingtemplates/`, {
        method: 'POST',
        body: template,
      });
    },
    async update(template: FindingTemplate) {
      return await $fetch<FindingTemplate>(`/api/v1/findingtemplates/${template.id}/`, {
        method: 'PATCH',
        body: template,
      });
    },
    async delete(template: FindingTemplate) {
      await $fetch(`/api/v1/findingtemplates/${template.id}/`, {
        method: 'DELETE',
      });
    },
    async createFromFinding(template: FindingTemplate, projectId: string) {
      return await $fetch<FindingTemplate>(`/api/v1/findingtemplates/fromfinding/`, {
        method: 'POST',
        body: {
          ...template,
          project: projectId
        },
      });
    },
    async fetchFieldDefinition() {
      this.fieldDefinition = await $fetch<FieldDefinitionDict>('/api/v1/findingtemplates/fielddefinition/', { method: 'GET' });
      return this.fieldDefinition;
    },
    async getFieldDefinition() {
      if (this.fieldDefinition !== null) {
        return this.fieldDefinition;
      } else if (this.getFieldDefinitionSync) {
        return await this.getFieldDefinitionSync;
      }

      try {
        this.getFieldDefinitionSync = this.fetchFieldDefinition();
        return await this.getFieldDefinitionSync;
      } finally {
        this.getFieldDefinitionSync = null;
      }
    },
  },
});
