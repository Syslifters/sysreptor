import { sortBy } from "lodash-es";
import type { TemplateFieldDefinition, FieldDefinition, FindingTemplate, ProjectType, FindingTemplateTranslation } from "#imports";

export const useTemplateStore = defineStore('templates', {
  state: () => ({
    fieldDefinition: null as (FieldDefinition[])|null,
    getFieldDefinitionSync: null as Promise<FieldDefinition[]>|null,
    designFilter: null as ProjectType|null,
  }),
  getters: {
    fieldDefinitionList(): TemplateFieldDefinition[] {
      if (!this.fieldDefinition) {
        return [];
      }

      const fieldFilterHiddenFields = useLocalSettings().templateFieldFilterHiddenFields;
      return sortBy(
        this.fieldDefinition.map(f => ({ 
          ...f,
          visible: !fieldFilterHiddenFields.includes(f.id), 
          used_in_designs: (f as any).used_in_designs || false,
        })),
        [
          d => ((this.designFilter?.finding_fields || []).map(f => f.id).indexOf(d.id) + 1) || 100000,
          d => d.used_in_designs ? 0 : 1,
          (d) => {
            const originOrder = { core: 1, predefined: 2, custom: 3 };
            return originOrder[d.origin] || 10;
          }
        ]);
    },
  },
  actions: {
    clear() {
      // Nothing to clear
    },
    async create(template: Partial<Omit<FindingTemplate, 'translations'> & { translations: Partial<FindingTemplateTranslation>[] }>) {
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
    async copy(template: FindingTemplate) {
      return await $fetch<FindingTemplate>(`/api/v1/findingtemplates/${template.id}/copy/`, {
        method: 'POST',
        body: {},
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
      this.fieldDefinition = await $fetch<FieldDefinition[]>('/api/v1/findingtemplates/fielddefinition/', { method: 'GET' });
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
    setDesignFilter(options: { design: ProjectType|null, clear?: boolean }) {
      const localSettings = useLocalSettings();

      if (options.design && options.design.id !== 'all') {
        this.designFilter = options.design;
        localSettings.templateFieldFilterDesign = options.design.id;
        if (options.clear) {
          localSettings.templateFieldFilterHiddenFields = this.fieldDefinitionList.map(f => f.id);
        }
        localSettings.templateFieldFilterHiddenFields = localSettings.templateFieldFilterHiddenFields.filter(fId => !options.design!.finding_fields.some(f => f.id === fId));
      } else {
        this.designFilter = null;
        localSettings.templateFieldFilterDesign = 'all';
        localSettings.templateFieldFilterHiddenFields = [];
      }
    },
  },
});
