import { sortBy } from "lodash-es";
import type { TemplateFieldDefinition, FieldDefinitionDict, FindingTemplate, ProjectType, FindingTemplateTranslation } from "~/utils/types";

export const useTemplateStore = defineStore('templates', {
  state: () => ({
    fieldDefinition: null as (FieldDefinitionDict)|null,
    getFieldDefinitionSync: null as Promise<FieldDefinitionDict>|null,
    designFilter: null as ProjectType|null,
  }),
  getters: {
    fieldDefinitionList(): TemplateFieldDefinition[] {
      if (!this.fieldDefinition) {
        return [];
      }

      const fieldFilterHiddenFields = useLocalSettings().templateFieldFilterHiddenFields;
      return sortBy(
        Object.keys(this.fieldDefinition).map(id => ({ 
          id, 
          visible: !fieldFilterHiddenFields.includes(id), 
          used_in_designs: (this.fieldDefinition![id] as any).used_in_designs,
          ...this.fieldDefinition![id]!,
        })),
        [
          d => ((this.designFilter?.finding_field_order || []).indexOf(d.id) + 1) || 100000,
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
    setDesignFilter(options: { design: ProjectType|null, clear?: boolean }) {
      const localSettings = useLocalSettings();

      if (options.design && options.design.id !== 'all') {
        this.designFilter = options.design;
        localSettings.templateFieldFilterDesign = options.design.id;
        if (options.clear) {
          localSettings.templateFieldFilterHiddenFields = this.fieldDefinitionList.map(f => f.id);
        }
        localSettings.templateFieldFilterHiddenFields = localSettings.templateFieldFilterHiddenFields.filter(f => !options.design!.finding_field_order.includes(f));
      } else {
        this.designFilter = null;
        localSettings.templateFieldFilterDesign = 'all';
        localSettings.templateFieldFilterHiddenFields = [];
      }
    },
  },
});
