<template>
  <v-container fluid>
    <split-menu v-model="menuSize">
      <template #menu>
        <v-list dense>
          <v-list-item>
            <v-select 
              v-model="fieldVisibilityFilter"
              label="Show fields of"
              :items="[{id: 'all', name: 'All Designs'}].concat(projectTypes.data)"
              item-value="id" item-text="name"
              :loading="projectTypes.isLoading"
            >
              <template #append-item>
                <div v-if="projectTypes.hasNextPage" v-intersect="projectTypes.fetchNextPage()" />
              </template>
            </v-select>
          </v-list-item>

          <v-list-item v-for="d in fieldDefinition" :key="d.id">
            <v-list-item-title>{{ d.id }}</v-list-item-title>
            <v-list-item-action v-if="d.origin !== 'core'">
              <s-btn @click="d.visible = !d.visible" icon x-small>
                <v-icon v-if="d.visible">mdi-eye</v-icon>
                <v-icon v-else>mdi-eye-off</v-icon>
              </s-btn>
            </v-list-item-action>
          </v-list-item>
        </v-list>
      </template>

      <template #default>
        <edit-toolbar v-bind="toolbarAttrs" v-on="toolbarEvents" :can-auto-save="true" />

        <div v-for="d in fieldDefinitionsCore" :key="d.id">
          <dynamic-input-field 
            v-model="template.data[d.id]" 
            :id="d.id" 
            :definition="d" 
            :selectable-users="[]" 
            :lang="template.language"
            :disabled="readonly"
          />
        </div>
        <language-selection v-model="template.language" :disabled="readonly" />
        <v-combobox
          v-model="template.tags"
          :items="templateTagSuggestions"
          :disabled="readonly"
          label="Tags"
          multiple
          chips deletable-chips
          outlined 
          hide-details="auto"
          class="mt-4"
          spellcheck="false"
        />
        <div v-for="d in visibleFieldDefinitionsExceptCore" :key="d.id">
          <dynamic-input-field 
            v-model="template.data[d.id]" 
            :id="d.id" 
            :definition="d" 
            :selectable-users="[]" 
            :lang="template.language"
            :disabled="readonly"
          />
        </div>
      </template>
    </split-menu>
  </v-container>
</template>

<script>
import DynamicInputField from '~/components/DynamicInputField.vue';
import { EditMode } from '~/components/EditToolbar.vue';
import LanguageSelection from '~/components/LanguageSelection.vue';
import SplitMenu from '~/components/SplitMenu.vue';
import LockEditMixin from '~/mixins/LockEditMixin';
import { CursorPaginationFetcher } from '~/utils/urls';

function getTemplateUrl(params) {
  return `/findingtemplates/${params.templateId}/`;
}

function compareOrigin(a, b) {
  const originOrder = { core: 1, predefined: 2, custom: 3 };
  return (originOrder[a.origin] || 10) - (originOrder[b.origin] || 10);
}

export default {
  components: { SplitMenu, DynamicInputField, LanguageSelection },
  mixins: [LockEditMixin],
  async asyncData({ params, store, $axios }) {
    const template = await $axios.$get(getTemplateUrl(params));
    const rawFieldDefinition = await store.dispatch('templates/getFieldDefinition');
    const fieldDefinition = Object.keys(rawFieldDefinition)
      .map(id => ({ id, visible: true, ...rawFieldDefinition[id] }))
      .sort(compareOrigin);
    return { template, fieldDefinition };
  },
  data() {
    return {
      editMode: (this.$auth.hasScope('template_editor')) ? EditMode.EDIT : EditMode.READONLY,
      projectTypes: new CursorPaginationFetcher('/projecttypes/', this.$axios, this.$toast),
    }
  },
  computed: {
    data() {
      return this.template;
    },
    deleteConfirmInput() {
      return this.template.data.title;
    },
    templateTagSuggestions() {
      return [
        'web', 'infrastructure', 'organizational', 'hardening', 'internal', 'external', 'third_party',
        'active_directory', 'windows', 'client', 
        'config', 'update', 'development', 'crypto',
      ];
    },
    visibleFieldDefinitions() {
      return this.fieldDefinition.filter(f => f.visible);
    },
    visibleFieldDefinitionsExceptCore() {
      return this.visibleFieldDefinitions.filter(f => f.origin !== 'core');
    },
    fieldDefinitionsCore() {
      return this.fieldDefinition.filter(f => f.origin === 'core');
    },
    fieldVisibilityFilter: {
      get() {
        return this.$store.state.settings.templateFieldVisibilityFilter;
      },
      set(val) {
        this.$store.commit('settings/updateTemplateFieldVisibilityFilter', val);
      }
    },
    menuSize: {
      get() {
        return this.$store.state.settings.templateInputMenuSize;
      },
      set(val) {
        this.$store.commit('settings/updateTemplateInputMenuSize', val);
      }
    },
  },
  watch: {
    fieldVisibilityFilter: {
      immediate: true,
      async handler(val) {
        if (val === 'all') {
          this.fieldDefinition.forEach((d) => {
            d.visible = true
          });
        } else {
          try {
            const projectType = await this.$store.dispatch('projecttypes/getById', val);
            this.fieldDefinition.forEach((d) => {
              d.visible = Object.keys(projectType.finding_fields).includes(d.id);
            });
          } catch (error) {
            this.$toast.global.requestError({ error });
            this.fieldVisibilityFilter = 'all';
          }
        }
      }
    },
  },
  methods: {
    getBaseUrl(data) {
      return getTemplateUrl({ templateId: data.id });
    },
    getHasEditPermissions() {
      return this.$auth.hasScope('template_editor');
    },
    async performSave(data) {
      await this.$store.dispatch('templates/update', data);
    },
    async performDelete(data) {
      await this.$store.dispatch('templates/delete', data)
      this.$router.push(`/templates/`);
    },
  }
}
</script>
